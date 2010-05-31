import unittest
import unicodedata
from robot.utils import unic, is_jython
from robot.utils.asserts import assert_equals, assert_true
if is_jython:
    from java.lang import String
    import JavaObject
    import UnicodeJavaLibrary


if is_jython:
    class TestJavaUnic(unittest.TestCase):

        def test_with_java_object(self):
            data = u'This is unicode \xe4\xf6'
            assert_equals(unic(JavaObject(data)), data)

        def test_with_class_type(self):
            assert_true('java.lang.String' in unic(String('').getClass()))

        def test_with_array_containing_unicode_objects(self):
            assert_true('Circle is 360' in
                        unic(UnicodeJavaLibrary().javaObjectArray()))

        def test_with_iterator(self):
            iterator = UnicodeJavaLibrary().javaIterator()
            assert_true('java.util' in unic(iterator))
            assert_true('Circle is 360' in iterator.next())


class TestUnic(unittest.TestCase):

    if not is_jython:
        def test_unicode_nfc_and_nfd_decomposition_equality(self):
            text = u'Hyv\xe4'
            assert_equals(unic(unicodedata.normalize('NFC', text)), text)
            # In Mac filesystem umlaut characters are presented in NFD-format.
            # This is to check that unic normalizes all strings to NFC 
            assert_equals(unic(unicodedata.normalize('NFD', text)), text)

    def test_object_containing_unicode_repr(self):
        assert_equals(unic(UnicodeRepr()), u'Hyv\xe4')

    def test_list_with_objects_containing_unicode_repr(self):
        objects = [UnicodeRepr(), UnicodeRepr()]
        if is_jython:
            expected = '[Hyv\\xe4, Hyv\\xe4]' # This is actually wrong behavior
        else:
            expected = "<unrepresentable object 'list'>"
        assert_equals(unic(objects), expected)


class UnicodeRepr:

    def __repr__(self):
        return u'Hyv\xe4'


if __name__ == '__main__':
    unittest.main()
