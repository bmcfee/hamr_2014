import whoosh
import whoosh.index
import whoosh.qparser
import cPickle as pickle
from pprint import pprint

id_to_name      = None
member_to_group = None
group_to_member = None

fulltext_index  = None
parser          = None

def init(CFG):
    
    global id_to_name
    global group_to_member
    global member_to_group
    global fulltext_index
    global parser

    with open(CFG['server']['id_to_name'], 'r') as f:
        id_to_name = pickle.load(f)

    with open(CFG['server']['group_to_member'], 'r') as f:
        group_to_member = pickle.load(f)
    
    with open(CFG['server']['member_to_group'], 'r') as f:
        member_to_group = pickle.load(f)

    fulltext_index = whoosh.index.open_dir(CFG['server']['fulltext'])
    parser = whoosh.qparser.MultifieldParser(['name', 'profile'], fulltext_index.schema)


def search(query=''):

    results = []

    with fulltext_index.searcher() as search: 
        results = [(r['artist_id'], r['name']) for r in search.search(parser.parse(unicode(query)), limit=15)]

    return results

