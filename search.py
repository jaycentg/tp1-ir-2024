from bsbi import BSBIIndex
from compression import VBEPostings, EliasGammaPostings

# sebelumnya sudah dilakukan indexing
# BSBIIndex hanya sebagai abstraksi untuk index tersebut
BSBI_instance = BSBIIndex(data_path = 'collection', \
                          postings_encoding = VBEPostings, \
                          output_path = 'index')

# untuk menggunakan index hasil Elias-Gamma encoding, dapat
# uncomment untuk potongan kode berikut
"""
BSBI_instance = BSBIIndex(data_path = 'collection', \
                          postings_encoding = EliasGammaPostings, \
                          output_path = 'index_eg')
""" 

queries = ["pupil mata", "aktor", "batu permata"]
for query in queries:
    print("Query  : ", query)
    print("Results:")
    for doc in BSBI_instance.boolean_retrieve(query):
        print(doc)
    print()