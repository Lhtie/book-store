import jieba
import os

stopwords_files = ["baidu_stopwords.txt", "cn_stopwords.txt", "hit_stopwords.txt", "scu_stopwords.txt"]

class Tokenizer():
    def __init__(self):
        this_path = os.path.abspath(__file__)
        this_dir = os.path.dirname(this_path)
        self.stop_words = set()
        for file in stopwords_files:
            with open(os.path.join(this_dir, "stopwords", file), "r", encoding="utf-8") as f:
                words = [word.strip() for word in f.readlines()]
                self.stop_words.update(set(words))

    def parse_author(self, author: str) -> (int, str):
        if not isinstance(author, str):
            return 528, ""
        top = 0
        text = ""
        for char in author:
            if char in "([（【「“{":
                top += 1
            elif char in ")]）】」”}":
                top -= 1
            elif top == 0:
                text += char
        if text == "":
            return 528, ""
        return 200, text
        
    def forward(self, raw: str) -> list:
        sentences = raw.split('\n')
        tokens_set = set()
        for sent in sentences:
            raw_tokens = jieba.cut(sent, cut_all=False)
            tokens = []
            for token in raw_tokens:
                token = token.strip()
                if not token in self.stop_words:
                    tokens.append(token)
            tokens_set.update(set(tokens))
        return list(tokens_set)