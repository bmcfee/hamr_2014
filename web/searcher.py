import whoosh
import whoosh.index
import whoosh.qparser
import cPickle as pickle

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

# 2014-01-26 03:24:34 by Brian McFee <brm2132@columbia.edu>
#  miles davis = 262586

def bfs_search(seed_id, max_depth=2):

    bfs_queue = [(0, seed_id)]

    vertices    = set()
    edges       = {}
    dmap        = {}

    while bfs_queue:
        distance, vertex_id = bfs_queue.pop(0)

        if vertex_id not in dmap:
            dmap[vertex_id] = distance

        if distance > max_depth:
            break

        vertices.add(vertex_id)
        
        if distance == max_depth:
            continue

        # Get all the edges for this vertex
        new_nodes = set()

        if vertex_id in member_to_group:
            new_nodes.update(member_to_group[vertex_id])

        if vertex_id in group_to_member:
            new_nodes.update(group_to_member[vertex_id])
        
        # Add the new nodes to the edge set
        for n in new_nodes:
            if vertex_id not in edges:
                edges[vertex_id] = set()

            edges[vertex_id].add(n)

            # Queue these new nodes for insertion into the graph
            bfs_queue.append( (1 + distance, n) )

    # Now we need to pack up the graph in a json-friendly format
    vertices = list(vertices)

    for k in edges:
        edges[k] = list(edges[k])

    vmap = {}
    nodes = []
    for index, vertex in enumerate(vertices):
        vmap[vertex] = index
#         group = 1
#         if vertex == seed_id:
#             group = 1
#         else:
#             group = 2 + int(vertex in group_to_member)

        nodes.append({  'name':     id_to_name[vertex], 
                        'id':       vertex,
                        'group':    dmap[vertex]})

    links = []
    for source in edges:
        for target in edges[source]:
            links.append( { 'source': vmap[source], 
                            'target': vmap[target],
                            'value': 1 })

    # Get the profile
    profile = ''
    with fulltext_index.searcher() as search: 
        profile = search.document(artist_id=seed_id)['profile']
        
    return {'nodes': nodes, 'links': links, 'profile': profile}

def search(query=''):

    results = []

    with fulltext_index.searcher() as search: 
        results = [{'artist_id': r['artist_id'], 'name': r['name']} for r in search.search(parser.parse(unicode(query)), limit=15)]

    return results

