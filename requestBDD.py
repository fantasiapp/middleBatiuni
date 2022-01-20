import sys
import os
package_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/var/fantasiapp/batiUni/middle/')
from bdd import executeRequest


def getEmbeddings():
    fields = ', '.join([f"e.dim{i+1}" for i in range(50)])
    query = f"SELECT j.name, {fields} FROM embeddings AS e JOIN (SELECT d.id, l.name FROM documents AS d JOIN labels AS l ON d.label_id = l.id) AS j ON j.id = e.doc_id"
    results = executeRequest(query, True)
    return ([row[0] for row in results], [row[1:] for row in results])
