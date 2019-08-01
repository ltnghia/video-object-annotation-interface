from PyQt5.QtCore import *

class StringBundle:
    __create_key = object()

    ids_to_messages_dict = {}

    def __init__(self, create_key):
        assert(create_key == StringBundle.__create_key), "StringBundle must be created using StringBundle.getBundle"
        self.__load('./resources/strings/strings.properties')

    @classmethod
    def get_bundle(cls):
        return StringBundle(cls.__create_key)

    def get_string(self, string_id):
        assert(string_id in self.ids_to_messages_dict), "Missing string id : " + string_id
        return self.ids_to_messages_dict[string_id]

    def __load(self, path):
        PROP_SEPERATOR = '='

        f = QFile(path)
        if not f.exists():
            return
        if f.open(QIODevice.ReadOnly | QFile.Text):
            text = QTextStream(f)
            text.setCodec('UTF-8')

        while not text.atEnd():
            line = str(text.readLine())
            key_value = line.split(PROP_SEPERATOR)
            key = key_value[0].strip()
            value = PROP_SEPERATOR.join(key_value[1:]).strip().strip('"')
            self.ids_to_messages_dict[key] = value

        f.close()
