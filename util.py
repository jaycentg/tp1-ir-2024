class IdMap:
    """
    Ingat kembali di kuliah, bahwa secara praktis, sebuah dokumen dan
    sebuah term akan direpresentasikan sebagai sebuah integer. Oleh
    karena itu, kita perlu maintain mapping antara string term (atau
    dokumen) ke integer yang bersesuaian, dan sebaliknya. Kelas IdMap ini
    akan melakukan hal tersebut.
    """

    def __init__(self):
        """
        Mapping dari string (term atau nama dokumen) ke id disimpan dalam
        python's dictionary; cukup efisien. Mapping sebaliknya disimpan dalam
        python's list.

        contoh:
            str_to_id["halo"] ---> 8
            str_to_id["/collection/dir0/gamma.txt"] ---> 54

            id_to_str[8] ---> "halo"
            id_to_str[54] ---> "/collection/dir0/gamma.txt"
        """
        self.str_to_id = {}
        self.id_to_str = []

    def __len__(self):
        """Mengembalikan banyaknya term (atau dokumen) yang disimpan di IdMap."""
        return len(self.str_to_id)

    def __get_id(self, s):
        """
        Mengembalikan integer id i yang berkorespondensi dengan sebuah string s.
        Jika s tidak ada pada IdMap, lalu assign sebuah integer id baru dan kembalikan
        integer id baru tersebut.
        """
        # Loop to find s in self.str_to_id. If s is found, return the id of s.
        for (string, item_id) in self.str_to_id.items():
            if string == s:
                return item_id

        # Assign new id to s (based on the current size of IdMap), insert to both
        # str_to_id and id_to_str, return the newly-assigned id.
        new_id = self.__len__()
        self.str_to_id[s] = new_id
        self.id_to_str.append(s)
        return new_id

    def __get_str(self, i):
        """Mengembalikan string yang terasosiasi dengan index i."""
        return self.id_to_str[i]

    def __getitem__(self, key):
        """
        __getitem__(...) adalah special method di Python, yang mengizinkan sebuah
        collection class (seperti IdMap ini) mempunyai mekanisme akses atau
        modifikasi elemen dengan syntax [..] seperti pada list dan dictionary di Python.

        Silakan search informasi ini di Web search engine favorit Anda. Saya mendapatkan
        link berikut:

        https://stackoverflow.com/questions/43627405/understanding-getitem-method

        """
        if type(key) == str:
            # Return id if the provided key is a string.
            return self.__get_id(key)
        else:
            # Return string if the provided key is an integer (id).
            return self.__get_str(key)

class QueryParser:
    """
    Class untuk melakukan parsing query untuk boolean search
    
    Parameters
    ----------
    query: str
        Query string yang akan di-parse. Input dijamin valid, tidak ada imbalanced parentheses.
        Tanda kurung buka dijamin "menempel" di awal kata yang mengikuti (atau tanda kurung buka lainnya) dan
        tanda kurung tutup dijamin "menempel" di akhir kata yang diikuti (atau tanda kurung tutup lainnya).
        Sebagai contoh, bisa lihat pada contoh method query_string_to_list() atau pada test case.
    stemmer
        Objek stemmer untuk stemming token
    stopwords: set
        Set yang berisi stopwords
    """
    def __init__(self, query: str, stemmer, stopwords: set):
        self.query = query
        self.stemmer = stemmer
        self.stopwords = stopwords
        self.query_list = self.query_string_to_list()
        self.query_preprocessed = self.preprocess_tokens()
    
    def is_valid(self):
        for token in self.query_list:
            if token in self.stopwords:
                return False
        return True

    def query_string_to_list(self):
        """
        Melakukan parsing query dari yang berbentuk string menjadi list of tokens.
        Contoh: "term1 AND term2 OR (term3 DIFF term4)" --> ["term1", "AND", "term2", "OR", "(",
                                                             "term3", "DIFF", "term4", ")"]

        Returns
        -------
        List[str]
            query yang sudah di-parse
        """        
        result = []
        for token in self.query_list:
            while token[0] == "(":
                result.append(token[0])
                token = token[1:]
            suffix_parentheses = []
            while token[-1] == ")":
                suffix_parentheses.append(token[-1])
                token = token[:-1]
            result.append(token)
            result.extend(suffix_parentheses)
        return result

    def preprocess_tokens(self):
        result = []
        for token in self.query_list:
            if token in ('AND', 'OR', 'DIFF', '(', ')'):
                result.append(token)
            else:
                stemmed = self.stemmer.stem(token.lower())
                # if stemmed in self.stopwords:
                #     stemmed = ""
                result.append(stemmed)
        return result

    def infix_to_postfix(self):
        """
        Fungsi ini mengubah ekspresi infix menjadi postfix. Evaluasi akan dilakukan secara postfix juga.
        Contoh: A AND B (infix) --> A B AND (postfix)
        Untuk selengkapnya, silakan lihat algoritma berikut: 
        https://www.geeksforgeeks.org/convert-infix-expression-to-postfix-expression/

        Returns
        -------
        list[str]
            list yang berisi token dalam ekspresi postfix
        """
        precedence = {'NOT': 1, 'AND': 1, 'OR': 1}
        output_queue = []
        operator_stack = []
        
        for token in self.query_preprocessed:
            if token in precedence:
                while (operator_stack and operator_stack[-1] != '(' and
                       precedence[operator_stack[-1]] >= precedence[token]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                if operator_stack and operator_stack[-1] == '(':
                    operator_stack.pop()
            else:
                output_queue.append(token)
        
        while operator_stack:
            output_queue.append(operator_stack.pop())

def sort_intersect_list(list_A, list_B):
    """
    Intersects two (ascending) sorted lists and returns the sorted result
    Melakukan Intersection dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-intersect.

    Returns
    -------
    List[Comparable]
        intersection yang sudah terurut
    """
    pointer_A = 0
    pointer_B = 0

    length_A = len(list_A)
    length_B = len(list_B)

    # Initialize an empty list to store result.
    answer = []

    # Loop until one list has been fully compared to another.
    while pointer_A < length_A and pointer_B < length_B:
        if list_A[pointer_A] == list_B[pointer_B]:
            # If certain value appears in both lists, append the value into answer list.
            answer.append(list_A[pointer_A])
            # Increase both pointers.
            pointer_A += 1
            pointer_B += 1
        elif list_A[pointer_A] < list_B[pointer_B]:
            # If the value being compared in list_A is "less" than the value being compared
            # in list_B, increase pointer for list_A.
            pointer_A += 1
        else:
            # Else, increase pointer for list_B.
            pointer_B += 1
    return answer

def sort_union_list(list_A, list_B):
    """
    Melakukan union dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-union.

    Returns
    -------
    List[Comparable]
        union yang sudah terurut
    """
    pointer_A = 0
    pointer_B = 0

    length_A = len(list_A)
    length_B = len(list_B)

    # Initialize an empty list to store result.
    answer = []

    # Loop until one list has been fully compared to another.
    while pointer_A < length_A and pointer_B < length_B:
        if list_A[pointer_A] == list_B[pointer_B]:
            answer.append(list_A[pointer_A])
            pointer_A += 1
            pointer_B += 1
        elif list_A[pointer_A] < list_B[pointer_B]:
            answer.append(list_A[pointer_A])
            pointer_A += 1
        else:
            answer.append(list_B[pointer_B])
            pointer_B += 1
    
    # append sisanya
    while pointer_A < length_A:
        answer.append(list_A[pointer_A])
        pointer_A += 1

    while pointer_B < length_B:
        answer.append(list_B[pointer_B])
        pointer_B += 1

    return answer

def sort_diff_list(list_A, list_B):
    """
    Melakukan difference dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-difference.

    Returns
    -------
    List[Comparable]
        difference yang sudah terurut
    """
    pointer_A = 0
    pointer_B = 0

    length_A = len(list_A)
    length_B = len(list_B)

    # Initialize an empty list to store result.
    answer = []

    # Loop until one list has been fully compared to another.
    while pointer_A < length_A and pointer_B < length_B:
        if list_A[pointer_A] == list_B[pointer_B]:
            pointer_A += 1
            pointer_B += 1
        elif list_A[pointer_A] < list_B[pointer_B]:
            answer.append(list_A[pointer_A])
            pointer_A += 1
        else:
            pointer_B += 1
    
    # append sisanya di list A
    while pointer_A < length_A:
        answer.append(list_A[pointer_A])
        pointer_A += 1

    return answer    

if __name__ == '__main__':
    doc = ["halo", "semua", "selamat", "pagi", "semua"]
    term_id_map = IdMap()
    assert [term_id_map[term] for term in doc] == [0, 1, 2, 3, 1], "term_id salah"
    assert term_id_map[1] == "semua", "term_id salah"
    assert term_id_map[0] == "halo", "term_id salah"
    assert term_id_map["selamat"] == 2, "term_id salah"
    assert term_id_map["pagi"] == 3, "term_id salah"

    docs = ["/collection/0/data0.txt",
            "/collection/0/data10.txt",
            "/collection/1/data53.txt"]
    doc_id_map = IdMap()
    assert [doc_id_map[docname] for docname in docs] == [0, 1, 2], "docs_id salah"

    assert sort_intersect_list([1, 2, 3], [2, 3]) == [2, 3], "sorted_intersect salah"
    assert sort_intersect_list([4, 5], [1, 4, 7]) == [4], "sorted_intersect salah"
    assert sort_intersect_list([], []) == [], "sorted_intersect salah"

    assert sort_union_list([1, 2, 3], [2, 3]) == [1, 2, 3], "sorted_union salah"
    assert sort_union_list([4, 5], [1, 4, 7]) == [1, 4, 5, 7], "sorted_union salah"
    assert sort_union_list([], []) == [], "sorted_union salah"

    assert sort_diff_list([1, 2, 3], [2, 3]) == [1], "sorted_diff salah"
    assert sort_diff_list([4, 5], [1, 4, 7]) == [5], "sorted_diff salah"
    assert sort_diff_list([], []) == [], "sorted_diff salah"

    from mpstemmer import MPStemmer
    qp = QueryParser("((term1 AND term2) OR term3) DIFF (term6 AND (term4 OR term5) DIFF (term7 OR term8))", MPStemmer(), set(["term1"]))
    assert qp.query_string_to_list() == ['(', '(', 'term1', 'AND', 'term2', ')', 'OR', 'term3', ')', 
                                     'DIFF', '(', 'term6', 'AND', '(', 'term4', 'OR', 'term5', 
                                     ')', 'DIFF', '(', 'term7', 'OR', 'term8', ')', ')'], "parsing to list salah"
    print(qp.preprocess_tokens())