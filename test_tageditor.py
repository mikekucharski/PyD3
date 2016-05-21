import unittest
from tageditor import musicTitle

class TestTagEditor(unittest.TestCase):

    def test_title_case(self):
        title = "I LiKe TyPiNg LiKe ThIs"
        self.assertEquals(musicTitle(title), "I Like Typing Like This")

    def test_title_with_spaces(self):
        title = "this   contains    spaces     "
        self.assertEquals(musicTitle(title), "This Contains Spaces")

    def test_title_with_quotes(self):
        title = "I 'am' isn't don't you're"
        self.assertEquals(musicTitle(title), "I 'am' Isn't Don't You're")

    def test_title_with_parans(self):
        title = "best title (ever)"
        self.assertEquals(musicTitle(title), "Best Title (Ever)")

    def test_title_with_lp(self):
        title = "marshall mathers lp"
        self.assertEquals(musicTitle(title), "Marshall Mathers LP")

    def test_title_with_ep(self):
        title = "my bands ep"
        self.assertEquals(musicTitle(title), "My Bands EP")

    def test_title_with_roman_num(self):
        self.assertEquals(musicTitle("version i"), "Version I")
        self.assertEquals(musicTitle("version ii"), "Version II")
        self.assertEquals(musicTitle("version iii"), "Version III")
        self.assertEquals(musicTitle("version iv"), "Version IV")
        self.assertEquals(musicTitle("version v"), "Version V")

    def test_title_with_special_case_parens(self):
        self.assertEquals(musicTitle("Version (iii)"), "Version (III)")
        self.assertEquals(musicTitle("(CAN'T)"), "(Can't)")
        self.assertEquals(musicTitle("test (ep)"), "Test (EP)")
        self.assertEquals(musicTitle("test (lp)"), "Test (LP)")

if __name__ == '__main__':
    unittest.main()