from abc import ABC, abstractmethod


class Modules(ABC):

    @abstractmethod
    def run(self):
        pass


class Aspell(Modules):

    # overriding abstract method to run aspell
    def run(self, buddy, file):
        import latexbuddy.aspell as aspell
        aspell.run(buddy, file)


class Languagetool(Modules):

    # overriding abstract method
    def run(self, buddy, file):
        import latexbuddy.languagetool as languagetool
        languagetool.run(buddy, file)


class Chktex(Modules):

    # overriding abstract method
    def run(self, buddy, file):
        import latexbuddy.chktex as chktex
        chktex.run(buddy, file)
