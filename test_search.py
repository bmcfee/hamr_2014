#!/usr/bin/env python

import whoosh, whoosh.index, whoosh.qparser
import sys
import pprint

if __name__ == '__main__':
    
    index = whoosh.index.open_dir(sys.argv[1])

    with index.searcher() as search:
        q = whoosh.qparser.MultifieldParser(['name', 'profile'], index.schema).parse(unicode(' '.join(sys.argv[2:])))
        results = search.search(q)
        if len(results) > 0:
            for r in results:
                pprint.pprint(r)
                print '---'
