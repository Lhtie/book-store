import jieba.posseg as pseg
from be.model.stopwords import stopwords

class Tokenizer():
    def __init__(self):
        self.stop_words = stopwords
        self.tokenizer = pseg.POSTokenizer(tokenizer=pseg.dt)

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
            raw_tokens = self.tokenizer.cut(sent)
            tokens = []
            for token, flag in raw_tokens:
                token = token.strip()
                if not token in self.stop_words:
                    if flag in ["n", "nr", "nz", "ns", "nt", "nw"]:
                        tokens.append(token)
            tokens_set.update(set(tokens))
        return list(tokens_set)