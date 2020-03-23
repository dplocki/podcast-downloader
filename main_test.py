import unittest
from main import file_name_to_entry_link_name


class TestLink2FileName(unittest.TestCase):

    def test_removing_date_from_downloaded_file(self):
        expected = 'file_name.mp3'
        result = file_name_to_entry_link_name(f'[20190701] {expected}')

        self.assertEqual(result, expected, f'File should be "{expected}" not "{result}"')


if __name__ == '__main__':
    unittest.main()
