if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from es import convert as convert_es
    from en import convert as convert_en
    convert_es.convert()
    convert_en.convert()

