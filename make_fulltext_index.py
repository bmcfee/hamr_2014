import lxml.etree
import lxml.objectify

import cPickle as pickle
import whoosh, whoosh.fields, whoosh.index, whoosh.analysis
from whoosh.support.charset import accent_map

import os

def formatXML(node):
    """
    Recursive operation which returns a tree formated
    as dicts and lists.
    Decision to add a list is to find the 'List' word
    in the actual parent tag.   
    """
    ret = {}
    if node.items(): 
        ret.update(dict(node.items()))
        
    if node.text: 
        ret['__content__'] = node.text
        
    for element in node:
        if element.tag not in ret:
            ret[element.tag] = []
        ret[element.tag].append(formatXML(element))
        
    # Flatten out any singletons
    for tag in ret:
        if isinstance(ret[tag], (list, tuple)) and len(ret[tag]) == 1:
            ret[tag] = ret[tag][0]
            
    if len(ret) == 1 and '__content__' in ret:
        return ret['__content__']
    
    return ret

def create_index_writer(index_path):

    if not os.path.exists(index_path):
        os.mkdir(index_path)
        pass

    A = whoosh.analysis.StemmingAnalyzer() | whoosh.analysis.CharsetFilter(accent_map)

    schema = whoosh.fields.Schema(  artist_id   =   whoosh.fields.NUMERIC(stored=True),
                                    name        =   whoosh.fields.TEXT(stored=True, analyzer=A),
                                    profile     =   whoosh.fields.TEXT(stored=True, analyzer=A))

    index = whoosh.index.create_in(index_path, schema)

    return index.writer()

def build_whoosh_index(root, index_path, good_ids):

    writer = create_index_writer(index_path)
    
    for i, artist in enumerate(root.iterchildren()):
        
        artist_struct = formatXML(artist)
        artist_id     = int(artist_struct['id'])
        if artist_id not in good_ids:
            continue
        name          = unicode(artist_struct['name'])
        
        if not isinstance(name, (str, unicode)):
            print 'BAD NAME: ', name
            continue
        
        profile = unicode(artist_struct.get('profile', ''))
        
        # Add to the woosh index
        print '%5d: %20s' % (artist_id, name)
        writer.add_document(artist_id=artist_id, name=name, profile=profile)
        
    writer.commit()


# Load the group/membership ids
good_ids = set()

with open('/home/bmcfee/git/hamr_2014/data/group_members.pickle', 'r') as f:
    good_ids.update(pickle.load(f).keys())

with open('/home/bmcfee/git/hamr_2014/data/member_to_group.pickle', 'r') as f:
    good_ids.update(pickle.load(f).keys())

tree = lxml.etree.parse('/home/bmcfee/data/discogs_20140101_artists.xml.gz')
build_whoosh_index(tree.getroot(), '/home/bmcfee/git/hamr_2014/data/fulltext', good_ids)
