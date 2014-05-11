
# Based on the idlparse.py example supplied with pyparsing.

from pyparsing import Literal, CaselessLiteral, Word, Upcase, OneOrMore,\
    ZeroOrMore, Forward, NotAny, delimitedList, oneOf, Group, Optional,\
    Combine, alphas, nums, restOfLine, cStyleComment, alphanums, printables,\
    empty, quotedString, ParseException, ParseResults, Keyword, Regex

from serf.idl_types import IDLType, InterfaceDef

def onType(toks):
    return IDLType(toks[0])

def onList(toks):
    return IDLType('list', toks[0][2])

def onFuture(toks):
    return IDLType('future', toks[0][2])

def onDict(toks):
    return IDLType('dict', toks[0][2])

def onOperation(toks):
    return [[toks[1], [t[1] for t in toks[3:-2]], toks[0]]]

def onInterfaceDef(toks):
    grouped = toks[0]
    # Probably failing as soon as we have base types.
    return InterfaceDef(grouped[1], grouped[3:-2])

bnf = None
def IDL_BNF():
    global bnf
    
    if not bnf:

        # punctuation
        colon  = Literal(":")
        lbrace = Literal("{")
        rbrace = Literal("}")
        lbrack = Literal("[")
        rbrack = Literal("]")
        lparen = Literal("(")
        rparen = Literal(")")
        equals = Literal("=")
        comma  = Literal(",")
        dot    = Literal(".")
        slash  = Literal("/")
        bslash = Literal("\\")
        star   = Literal("*")
        semi   = Literal(";")
        langle = Literal("<")
        rangle = Literal(">")
        
        # keywords
        ascii_     = Keyword("ascii")
        attribute_ = Keyword("attribute")
        bool_      = Keyword("bool")
        case_      = Keyword("case")
        byte_      = Keyword("byte")
        const_     = Keyword("const")
        context_   = Keyword("context")
        default_   = Keyword("default")
        data_      = Keyword("data")
        dict_      = Keyword("dict")
        enum_      = Keyword("enum")
        exception_ = Keyword("exception")
        false_     = Keyword("FALSE")
        fixed_     = Keyword("fixed")
        float_     = Keyword("float")
        inout_     = Keyword("inout")
        future_    = Keyword("future")
        interface_ = Keyword("interface")
        in_        = Keyword("in")
        int_       = Keyword("int")
        list_      = Keyword("list")
        long_      = Keyword("long")
        module_    = Keyword("module")
        object_    = Keyword("Object")
        oneway_    = Keyword("oneway")
        out_       = Keyword("out")
        raises_    = Keyword("raises")
        readonly_  = Keyword("readonly")
        struct_    = Keyword("struct")
        switch_    = Keyword("switch")
        text_      = Keyword("text")
        time_      = Keyword("time")
        true_      = Keyword("TRUE")
        typedef_   = Keyword("typedef")
        unsigned_  = Keyword("unsigned")
        union_     = Keyword("union")
        var_       = Keyword("var")
        void_      = Keyword("void")
        wchar_     = Keyword("wchar")
        wstring_   = Keyword("wstring")
        
        identifier = Word( alphas, alphanums + "_" ).setName("identifier")
        
        #~ real = Combine( Word(nums+"+-", nums) + dot + Optional( Word(nums) ) 
                        #~ + Optional( CaselessLiteral("E") + Word(nums+"+-",nums) ) )
        real = Regex(r"[+-]?\d+\.\d*([Ee][+-]?\d+)?").setName("real")
        #~ integer = ( Combine( CaselessLiteral("0x") + Word( nums+"abcdefABCDEF" ) ) |
                    #~ Word( nums+"+-", nums ) ).setName("int")
        integer = Regex(r"0x[0-9a-fA-F]+|[+-]?\d+").setName("Int")

        udTypeName = delimitedList( identifier, "::", combine=True ).setName("udType")
        # have to use longest match for type, in case a user-defined type name starts with a keyword type, like "stringSeq" or "longArray"
        typeName = ( bool_ ^ byte_ ^ float_ ^ int_ ^ long_ ^
                     ascii_ ^ text_ ^ data_ ^ time_ ^
                     var_ ^ udTypeName ).setName("type")
        typeName.setParseAction(onType)
        void_.setParseAction(onType)

        listDef = Forward().setName("seq")
        dictDef = Forward().setName("dict")
        futureDef = Forward().setName("future")

        typeDef = (listDef | dictDef | futureDef | typeName)
        
        listDef << Group( list_ + langle + typeDef + rangle )
        listDef.setParseAction(onList)

        futureDef << Group( future_ + langle + typeDef + rangle )
        futureDef.setParseAction(onFuture)

        dictDef << Group( dict_ + langle + typeDef + rangle )
        dictDef.setParseAction(onDict)


        typedefDef = Group( typedef_ + typeDef + identifier + semi ).setName("typedef")

        constDef = Group( const_ + typeDef + identifier + equals + ( real | integer | quotedString ) + semi ) #| quotedString )
        exceptionItem = Group( typeDef + identifier + semi )
        exceptionDef = ( exception_ + identifier + lbrace + ZeroOrMore( exceptionItem ) + rbrace + semi )
        attributeDef = Optional( readonly_ ) + attribute_ + typeName + identifier + semi
        paramlist = delimitedList( Group( ( inout_ | in_ | out_ ) + typeDef + identifier ) ).setName( "paramlist" )

        operationDef = (
            ( void_ ^ typeDef ) + identifier +
            lparen + Optional( paramlist ) + rparen +
            Optional( raises_ + lparen +
                      Group( delimitedList( typeName ) ) +
                      rparen ) + semi )
        operationDef.setParseAction(onOperation)

        interfaceItem = ( constDef | exceptionDef | attributeDef | operationDef )
        interfaceDef = Group( interface_ + identifier  + Optional( colon + delimitedList( typeName ) ) + lbrace + \
                        ZeroOrMore( interfaceItem ) + rbrace + semi ).setName("opnDef")
        interfaceDef.setParseAction(onInterfaceDef)

        moduleDef = Forward()
        moduleItem = ( interfaceDef | exceptionDef | constDef | typedefDef | moduleDef )
        moduleDef << module_ + identifier + lbrace + ZeroOrMore( moduleItem ) + rbrace + semi

        bnf = ( moduleDef | OneOrMore( moduleItem ) )
        
        singleLineComment = "//" + restOfLine
        bnf.ignore( singleLineComment )
        bnf.ignore( cStyleComment )
        
    return bnf

