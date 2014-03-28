
import re

import memdam

@memdam.tracer
def function_to_call(thing):
    value_class = ArbitraryClassWithFunctionsAndData(1, 2)
    class_to_call = ArbitraryClassWithFunctionsAndData(None, value_class)
    return class_to_call.some_function("a", "b", kwarg2=re.compile("great regex"))

class ArbitraryClassWithFunctionsAndData(memdam.Base):
    def __init__(self, val1, val2):
        self.val1 = val1
        self.val2 = val2
        
    def some_function(self, thing, other_thing, kwarg1=None, kwarg2=4):
        self.do_stuff(other_thing)
        return 4
    
    def do_stuff(self, other_thing):
        return "inner return value string thingy"
    
    def uh_oh(self, data):
        raise Exception("Data is too data-y: " + str(data))
    
def test_tracing():
    function_to_call([ArbitraryClassWithFunctionsAndData(4, 4), ArbitraryClassWithFunctionsAndData(4, 4), 1, 1, 1, 1, 2, 2, "suuuuuupppperlonnnngggstrrriinngggg" * 400])
    
if __name__ == '__main__':
    memdam.log.setLevel(memdam.TRACE)
    test_tracing()
    