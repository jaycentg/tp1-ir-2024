import array
import math

from bitarray import bitarray


class StandardPostings:
    """ 
    Class dengan static methods, untuk mengubah representasi postings list
    yang awalnya adalah List of integer, berubah menjadi sequence of bytes.
    Kita menggunakan Library array di Python.

    ASUMSI: postings_list untuk sebuah term MUAT di memori!

    Silakan pelajari:
        https://docs.python.org/3/library/array.html
    """

    @staticmethod
    def encode(postings_list):
        """
        Encode postings_list menjadi stream of bytes

        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)

        Returns
        -------
        bytes
            bytearray yang merepresentasikan urutan integer di postings_list
        """
        # Untuk yang standard, gunakan L untuk unsigned long, karena docID
        # tidak akan negatif. Dan kita asumsikan docID yang paling besar
        # cukup ditampung di representasi 4 byte unsigned.
        return array.array('L', postings_list).tobytes()

    @staticmethod
    def decode(encoded_postings_list):
        """
        Decodes postings_list dari sebuah stream of bytes

        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray merepresentasikan encoded postings list sebagai keluaran
            dari static method encode di atas.

        Returns
        -------
        List[int]
            list of docIDs yang merupakan hasil decoding dari encoded_postings_list
        """
        decoded_postings_list = array.array('L')
        decoded_postings_list.frombytes(encoded_postings_list)
        return decoded_postings_list.tolist()


class VBEPostings:
    """ 
    Berbeda dengan StandardPostings, dimana untuk suatu postings list,
    yang disimpan di disk adalah sequence of integers asli dari postings
    list tersebut apa adanya.

    Pada VBEPostings, kali ini, yang disimpan adalah gap-nya, kecuali
    posting yang pertama. Barulah setelah itu di-encode dengan Variable-Byte
    Enconding algorithm ke bytestream.

    Contoh:
    postings list [34, 67, 89, 454] akan diubah dulu menjadi gap-based,
    yaitu [34, 33, 22, 365]. Barulah setelah itu di-encode dengan algoritma
    compression Variable-Byte Encoding, dan kemudian diubah ke bytesream.

    ASUMSI: postings_list untuk sebuah term MUAT di memori!

    """

    @staticmethod
    def encode(postings_list):
        """
        Encode postings_list menjadi stream of bytes (dengan Variable-Byte
        Encoding). JANGAN LUPA diubah dulu ke gap-based list, sebelum
        di-encode dan diubah ke bytearray.

        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)

        Returns
        -------
        bytes
            bytearray yang merepresentasikan urutan integer di postings_list
        """
        # Intialize an empty gap-based list and initial doc_id.
        gap_based_list = []
        prev_doc_id = 0

        for doc_id in postings_list:
            if len(gap_based_list) == 0:
                # Append the first doc_id.
                gap_based_list.append(doc_id)
            else:
                # Append the gap size of current doc id with the previous one.
                gap_based_list.append(doc_id - prev_doc_id)
            # Update previous doc id.
            prev_doc_id = doc_id

        # Encode gap-based list with VB Encoding.
        return VBEPostings.vb_encode(gap_based_list)

    @staticmethod
    def vb_encode(list_of_numbers):
        """ 
        Melakukan encoding (tentunya dengan compression) terhadap
        list of numbers, dengan Variable-Byte Encoding
        """
        bytestream = []
        for num in list_of_numbers:
            # Encode each number using VB and extend it to bytestream list.
            encoded = VBEPostings.vb_encode_number(num)
            bytestream.extend(encoded)
        # Save as bytes.
        return array.array('B', bytestream).tobytes()

    @staticmethod
    def vb_encode_number(number):
        """
        Encodes a number using Variable-Byte Encoding
        Lihat buku teks kita!
        """
        bytes_number = []
        while True:
            bytes_number.insert(0, number % 128)
            if number < 128:
                break
            number = number // 128
        bytes_number[-1] += 128
        return bytes_number

    @staticmethod
    def decode(encoded_postings_list):
        """
        Decodes postings_list dari sebuah stream of bytes. JANGAN LUPA
        bytestream yang di-decode dari encoded_postings_list masih berupa
        gap-based list.

        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray merepresentasikan encoded postings list sebagai keluaran
            dari static method encode di atas.

        Returns
        -------
        List[int]
            list of docIDs yang merupakan hasil decoding dari encoded_postings_list
        """
        gap_based_list = VBEPostings.vb_decode(encoded_postings_list)
        result_list = []
        for i in range(0, len(gap_based_list)):
            if i == 0:
                result_list.append(gap_based_list[i])
            else:
                result_list.append(result_list[i - 1] + gap_based_list[i])
        return result_list

    @staticmethod
    def vb_decode(encoded_bytestream):
        """
        Decoding sebuah bytestream yang sebelumnya di-encode dengan
        variable-byte encoding.
        """
        numbers = []
        n = 0
        for byte in encoded_bytestream:
            if byte < 128:
                n = 128 * n + byte
            else:
                n = 128 * n + byte - 128
                numbers.append(n)
                n = 0
        return numbers


class EliasGammaPostings:
    @staticmethod
    def eg_encode_number(number):
        """
        https://stackoverflow.com/questions/16926130/convert-to-binary-and-keep-leading-zeros
        """
        if number == 0:
            return '0'

        N = math.floor(math.log(number, 2))
        head = '0' * N + '1'
        tail = format(number - 2 ** N, '#0{}b'.format(N + 2))[2:]

        return bitarray(head + tail)

    @staticmethod
    def encode(postings_list):
        """
        Encode postings_list using Elias Gamma encoding.

        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)

        Returns
        -------
        bytes
            bytearray representing the Elias Gamma encoded sequence of integers
        """
        result = bitarray()
        for num in postings_list:
            result.extend(EliasGammaPostings.eg_encode_number(num))
        return result

    @staticmethod
    def decode(encoded_postings_list):
        """
        Decode postings_list from a stream of bytes using Elias Gamma decoding.

        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray representing the Elias Gamma encoded sequence of integers.

        Returns
        -------
        List[int]
            List of docIDs resulting from decoding the encoded_postings_list.
        """
        decoded_numbers = []
        N = 0
        while len(encoded_postings_list) != 0:
            if encoded_postings_list[0] == 1:
                binary_after_one = encoded_postings_list[1:N + 1]
                K = int(str(binary_after_one.to01()), 2)
                decoded_numbers.append(2 ** N + K)
                encoded_postings_list = encoded_postings_list[N + 1:]
                N = 0
            else:
                N += 1
                encoded_postings_list = encoded_postings_list[1:]

        return decoded_numbers


if __name__ == '__main__':
    postings_list = [34, 67, 89, 454, 2345738]
    for Postings in [StandardPostings, VBEPostings]:
        print(Postings.__name__)
        encoded_postings_list = Postings.encode(postings_list)
        print("byte hasil encode: ", encoded_postings_list)
        print("ukuran encoded postings: ", len(encoded_postings_list), "bytes")
        decoded_posting_list = Postings.decode(encoded_postings_list)
        print("hasil decoding: ", decoded_posting_list)
        assert decoded_posting_list == postings_list, "hasil decoding tidak sama dengan postings original"
        print()
