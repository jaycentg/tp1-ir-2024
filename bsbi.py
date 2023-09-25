import os
import pickle
import contextlib
import heapq
import time

from index import InvertedIndexReader, InvertedIndexWriter
from util import IdMap, sort_intersect_list
from compression import StandardPostings, VBEPostings
from mpstemmer import MPStemmer
import re
import requests
import string


def sort_intersect_conjunctive(lists):
    # Assume that lists contain lists of list sorted by the length of the list
    if len(lists) == 1:
        return lists[0]

    results = lists[0]
    terms = lists[1:]

    while terms is not None and results is not None:
        results = sort_intersect_list(results, terms[0])
        terms = lists[1:] if len(terms) > 1 else None

    return results


""" 
Ingat untuk install tqdm terlebih dahulu
pip intall tqdm
"""
from tqdm import tqdm


class BSBIIndex:
    """
    Attributes
    ----------
    term_id_map(IdMap): Untuk mapping terms ke termIDs
    doc_id_map(IdMap): Untuk mapping relative paths dari dokumen (misal,
                    /collection/0/gamma.txt) to docIDs
    data_path(str): Path ke data
    output_path(str): Path ke output index files
    postings_encoding: Lihat di compression.py, kandidatnya adalah StandardPostings,
                    VBEPostings, dsb.
    index_name(str): Nama dari file yang berisi inverted index
    """

    def __init__(self, data_path, output_path, postings_encoding, index_name="main_index"):
        self.term_id_map = IdMap()
        self.doc_id_map = IdMap()
        self.data_path = data_path
        self.output_path = output_path
        self.index_name = index_name
        self.postings_encoding = postings_encoding

        # Untuk menyimpan nama-nama file dari semua intermediate inverted index
        self.intermediate_indices = []

    def save(self):
        """Menyimpan doc_id_map and term_id_map ke output directory via pickle"""

        with open(os.path.join(self.output_path, 'terms.dict'), 'wb') as f:
            pickle.dump(self.term_id_map, f)
        with open(os.path.join(self.output_path, 'docs.dict'), 'wb') as f:
            pickle.dump(self.doc_id_map, f)

    def load(self):
        """Memuat doc_id_map and term_id_map dari output directory"""

        with open(os.path.join(self.output_path, 'terms.dict'), 'rb') as f:
            self.term_id_map = pickle.load(f)
        with open(os.path.join(self.output_path, 'docs.dict'), 'rb') as f:
            self.doc_id_map = pickle.load(f)

    def start_indexing(self):
        """
        Base indexing code
        BAGIAN UTAMA untuk melakukan Indexing dengan skema BSBI (blocked-sort
        based indexing)

        Method ini scan terhadap semua data di collection, memanggil parse_block
        untuk parsing dokumen dan memanggil invert_write yang melakukan inversion
        di setiap block dan menyimpannya ke index yang baru.
        """
        # loop untuk setiap sub-directory di dalam folder collection (setiap block)
        for block_path in tqdm(sorted(next(os.walk(self.data_path))[1])):
            td_pairs = self.parsing_block(block_path)
            index_id = 'intermediate_index_' + block_path
            self.intermediate_indices.append(index_id)
            with InvertedIndexWriter(index_id, self.postings_encoding, path=self.output_path) as index:
                self.write_to_index(td_pairs, index)
                td_pairs = None

        self.save()

        with InvertedIndexWriter(self.index_name, self.postings_encoding, path=self.output_path) as merged_index:
            with contextlib.ExitStack() as stack:
                indices = [
                    stack.enter_context(InvertedIndexReader(index_id, self.postings_encoding, path=self.output_path))
                    for index_id in self.intermediate_indices]
                self.merge_index(indices, merged_index)

    def get_stop_words(self):
        # Using Satya stopwords
        # Fetch data from GitHub and split data by newline (\n)
        URL = 'https://raw.githubusercontent.com/datascienceid/stopwords-bahasa-indonesia/master/stopwords_id_satya.txt'
        r = requests.get(URL)
        return r.text.split("\n")

    def parsing_block(self, block_path):
        """
        Lakukan parsing terhadap text file sehingga menjadi sequence of
        <termID, docID> pairs.

        Gunakan tools available untuk Stemming Bahasa Indonesia Seperti
        MpStemmer: https://github.com/ariaghora/mpstemmer 
        Jangan gunakan PySastrawi untuk stemming karena kode yang tidak efisien dan lambat.

        JANGAN LUPA BUANG STOPWORDS! Kalian dapat menggunakan PySastrawi 
        untuk menghapus stopword atau menggunakan sumber lain seperti:
        - Satya (https://github.com/datascienceid/stopwords-bahasa-indonesia)
        - Tala (https://github.com/masdevid/ID-Stopwords)

        Untuk "sentence segmentation" dan "tokenization", bisa menggunakan
        regex atau boleh juga menggunakan tools lain yang berbasis machine
        learning.

        Parameters
        ----------
        block_path : str
            Relative Path ke directory yang mengandung text files untuk sebuah block.

            CATAT bahwa satu folder di collection dianggap merepresentasikan satu block.
            Konsep block di soal tugas ini berbeda dengan konsep block yang terkait
            dengan operating systems.

        Returns
        -------
        List[Tuple[Int, Int]]
            Returns all the td_pairs extracted from the block
            Mengembalikan semua pasangan <termID, docID> dari sebuah block (dalam hal
            ini sebuah sub-direktori di dalam folder collection)

        Harus menggunakan self.term_id_map dan self.doc_id_map untuk mendapatkan
        termIDs dan docIDs. Dua variable ini harus persis untuk semua pemanggilan
        parse_block(...).
        """
        stemmer = MPStemmer()
        tokenizer_pattern = r'\w+'
        satya_stop_words = set(self.get_stop_words())
        PUNCTUATION = string.punctuation

        td_pairs = []

        for filename in os.listdir(os.path.join(self.data_path, block_path)):
            document_path = os.path.join(self.data_path, block_path, filename)
            doc_id = self.doc_id_map[document_path]

            with open(document_path, 'r', encoding='utf-8') as file:
                content = file.read()

                # Tokenize content
                tokens_parsed = re.findall(tokenizer_pattern, content)

                # Stem token and convert to lowercase
                stemmed_tokens = [stemmer.stem(token.lower()) for token in tokens_parsed \
                                  if token not in PUNCTUATION]

                # Exclude stopwords from list of tokens
                filtered_tokens = [token for token in stemmed_tokens if token not in satya_stop_words]

                # Append (term_id, doc_id) pair for every filtered token
                for token in filtered_tokens:
                    term_id = self.term_id_map[token]
                    td_pairs.append((term_id, doc_id))

        return td_pairs

    def write_to_index(self, td_pairs, index):
        """
        Melakukan inversion td_pairs (list of <termID, docID> pairs) dan
        menyimpan mereka ke index. Disini diterapkan konsep BSBI dimana 
        hanya di-mantain satu dictionary besar untuk keseluruhan block.
        Namun dalam teknik penyimpanannya digunakan srategi dari SPIMI
        yaitu penggunaan struktur data hashtable (dalam Python bisa
        berupa Dictionary)

        ASUMSI: td_pairs CUKUP di memori

        Parameters
        ----------
        td_pairs: List[Tuple[Int, Int]]
            List of termID-docID pairs
        index: InvertedIndexWriter
            Inverted index pada disk (file) yang terkait dengan suatu "block"
        """
        term_dict = {}
        for term_id, doc_id in td_pairs:
            if term_id not in term_dict:
                term_dict[term_id] = set()
            term_dict[term_id].add(doc_id)
        for term_id in sorted(term_dict.keys()):
            index.append(term_id, sorted(list(term_dict[term_id])))

    def merge_index(self, indices, merged_index):
        """
        Lakukan merging ke semua intermediate inverted indices menjadi
        sebuah single index.

        Ini adalah bagian yang melakukan EXTERNAL MERGE SORT

        Parameters
        ----------
        indices: List[InvertedIndexReader]
            A list of intermediate InvertedIndexReader objects, masing-masing
            merepresentasikan sebuah intermediate inveted index yang iterable
            di sebuah block.

        merged_index: InvertedIndexWriter
            Instance InvertedIndexWriter object yang merupakan hasil merging dari
            semua intermediate InvertedIndexWriter objects.
        """
        # Loop for every term
        for i in range(len(self.term_id_map)):
            list_of_postings_list = []
            for index in indices:
                # Find the postings list for every term in every intermediate indices
                list_of_postings_list.append(index.get_postings_list(i))
            # Merge using heap and append to merged_index
            sorted_list = list(heapq.merge(*list_of_postings_list))
            merged_index.append(i, sorted_list)

    def boolean_retrieve(self, query):
        """
        Melakukan boolean retrieval untuk mengambil semua dokumen yang
        mengandung semua kata pada query. Jangan lupa lakukan pre-processing
        yang sama dengan yang dilakukan pada proses indexing!
        (Stemming dan Stopwords Removal)

        Parameters
        ----------
        query: str
            Query tokens yang dipisahkan oleh spasi

            contoh: Query "universitas indonesia depok" artinya adalah
                    boolean query "universitas AND indonesia AND depok"

        Returns
        ------
        List[str]
            Daftar dokumen terurut yang mengandung sebuah query tokens.
            Harus mengembalikan EMPTY LIST [] jika tidak ada yang match.

        JANGAN LEMPAR ERROR/EXCEPTION untuk terms yang TIDAK ADA di collection.
        """
        # Load metadata
        self.load()

        stemmer = MPStemmer()
        satya_stop_words = set(self.get_stop_words())
        PUNCTUATION = string.punctuation
        term_postings_list = []

        # Split tokens by whitespace
        split_tokens = query.split()

        # Stem token and convert to lowercase
        stemmed_tokens = [stemmer.stem(token.lower()) for token in split_tokens \
                          if token not in PUNCTUATION]

        # Exclude stopwords from list of tokens
        filtered_tokens = [token for token in stemmed_tokens if token not in satya_stop_words]

        with InvertedIndexReader(self.index_name, self.postings_encoding, self.output_path) as index:
            # Get postings list for every term, append to term_postings_list
            for term in filtered_tokens:
                term_id = self.term_id_map[term]
                postings_list = index.get_postings_list(term_id)
                term_postings_list.append(postings_list)

        # Sort list of lists based on the length of postings_list
        # Using in-place sorting to reduce space usage
        term_postings_list.sort(key=len)

        # Find the intersection of several postings lists (sorted)
        list_of_doc_id = sort_intersect_conjunctive(term_postings_list)
        result = []
        for doc_id in list_of_doc_id:
            # Append directory of document to result
            result.append(self.doc_id_map[doc_id])
        return result


if __name__ == "__main__":
    BSBI_instance = BSBIIndex(data_path='collections', \
                              postings_encoding=VBEPostings, \
                              output_path='index')
    BSBI_instance.start_indexing()  # memulai indexing!
