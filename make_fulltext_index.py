#!/usr/bin/env python

import argparse
import cPickle as pickle
import os
import sys

import lxml.etree

import whoosh, whoosh.fields, whoosh.index, whoosh.analysis
from whoosh.support.charset import accent_map

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
    '''Create a new whoosh index in the given directory path'''
    
    if not os.path.exists(index_path):
        os.mkdir(index_path)
        pass

    A = whoosh.analysis.StemmingAnalyzer() | whoosh.analysis.CharsetFilter(accent_map)

    schema = whoosh.fields.Schema(  artist_id   =   whoosh.fields.NUMERIC(stored=True),
                                    name        =   whoosh.fields.TEXT(stored=True, field_boost=8.0, analyzer=A),
                                    profile     =   whoosh.fields.TEXT(stored=True, analyzer=A))

    index = whoosh.index.create_in(index_path, schema)

    return index.writer()


def build_whoosh_index(root, index_path, good_ids):
    '''Populate the whoosh index from the XML tree'''

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
def populate_whoosh(group_members=None, members_to_group=None, discogs_xml=None,
                    whoosh_dir=None):
    '''Popular the whoosh database using only artists with degree 1 or higher'''

    good_ids = set()

    with open(group_members, 'r') as f:
        good_ids.update(pickle.load(f).keys())

    with open(members_to_group, 'r') as f:
        good_ids.update(pickle.load(f).keys())

    tree = lxml.etree.parse(discogs_xml)

    build_whoosh_index(tree.getroot(), whoosh_dir, good_ids)

def process_arguments():
    '''Process command-line arguments'''

    parser = argparse.ArgumentParser(description='Discogs artist xml to whoosh fulltext')

    parser.add_argument('group_members',    action='store',
                        help    = 'path to the group_members.pickle file')
    
    parser.add_argument('members_to_group',    action='store',
                        help    = 'path to the members_to_group.pickle file')

    parser.add_argument('discogs_xml',    action='store',
                        help    = 'path to the Discogs artist xml file')

    parser.add_argument('whoosh_dir',    action='store',
                        help    = 'path to build the whoosh fulltext index')

    return vars(parser.parse_args(sys.argv[1:]))

if __name__ == '__main__':
    args = process_arguments()

    populate_whoosh(**args)
