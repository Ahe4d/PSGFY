from __future__ import print_function
import sys
import os
import copy

from torque_vm_values import *

def pretty_print_function(function_name, namespace="", arguments=None, call_type="FunctionCall"):
    if arguments is None:
        arguments = []

    # Sanitize arguments. Their name may be omitted if they are unused.
    for i in range(0, len(arguments)):
        if not arguments[i]:
            arguments[i] = "%%unused_var_%d" % i

    function_call = "%s::" % namespace if namespace != "" else ""
    if call_type == "MethodCall" and len(arguments) > 0:
        if " " in arguments[0]:  # The caller name may have been constructed dynamically, i.e. (Objh @ "andle").call()
            function_call += "(%s)." % arguments[0]
        else:
            function_call += "%s." % arguments[0]
        arguments = arguments[1:]
    function_call += "%s(" % function_name
    if len(arguments) == 0:
        function_call += ")"
    else:
        for arg in arguments:
            function_call += "%s, " % arg if arg is not arguments[-1] else "%s)" % arg
    return function_call


def is_number(s):
    """
    Checks whether the contents of a string are actually a number.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def weirddecomp(dso, sink=None, in_function=False, offset=0, outdir="", nofolder=0, indent=0):
    """
    Decompiles the DSO object given as parameter.
    @param  dso         The object to decompile
    @param  sink        A file object in which the decompiled code will be written. Default is stdout.
    @param  in_function Whether the code to decompile is located in a function.
                        Do not use. It is only relevant to partial decompilations.
    @param  offset      An offset to apply to absolute jumps.
                        Do not use. It is only relevant to partial decompilations.
    """
    ste_size = 1
    ip = 0
    string_stack = []
    int_stack = []
    float_stack = []
    arguments = []
    binary_stack = []  # No counterpart in the VM. Used to keep track of binary operations.
    current_variable = None
    current_field = None
    current_object = None
    indentation = indent
    enable_debug = 0
    in_obj_create = 0
    in_while = 0
    print_me = 0
    varSink = sink
    oo = ""
    #print(nofolder)
    previous_opcodes = ["OP_INVALID", "OP_INVALID", "OP_INVALID", "OP_INVALID", "OP_INVALID"]

    # The big switch-case
    while ip < len(dso.code):
        opcode = get_opcode(dso.version, dso.code[ip])
        if opcode == "OP_IGNORE":
            if print_me:
                print("IGNORE HIT", file=sink)
        if print_me:
            print("[" + str(ip) + "] " + opcode, file=sink)
       # print(string_stack)
        if not opcode:
            raise ValueError("Encountered a value which does not translate to an opcode (%d)." % dso.code[ip])
        #print("[" + str(ip) + "]", file=sink)
        ip += 1
## START OF FUNCTION HANDLERS ##
        if opcode == "OP_FUNC_DECL":
            fnName = dso.get_string(dso.code[ip])
            fnNamespace  = dso.get_string(dso.code[ip + 1])
            fnPackage = dso.get_string(dso.code[ip + 2])
            has_body = dso.code[ip + 3]
            fnEndLoc = dso.code[ip + 4]
            argc = dso.code[ip + 5]
            argv = []
            indentation += 1
            in_function = True
            if dso.code[ip + 1] == 0:
                fnNamespace = ""
            if not nofolder:
                if fnNamespace != "":
                    oo = outdir + "/" + fnNamespace + "-" + fnName + ".cs"
                else:
                    oo = outdir + "/" + fnName + ".cs"
                sink = open(oo, 'w')
            #print("fnName " + fnName)
            #print("fnNamespace " + fnNamespace)
            #print("fnPackage " + fnPackage)
            #print("has a body? " + str(has_body))
            #print("end ip == " + str(fnEndLoc))
            if fnName == "onExplode" and fnNamespace == "ProjectileData":
                print_me = 0
                enable_debug = 0
            #print("argc == " + str(argc))
            dso.code.insert(fnEndLoc, METADATA["META_ENDFUNC"])
            for i in range(0, argc):
                argv.append(dso.get_string(dso.code[ip + 3*1 + 3 + 1*i]))
            print("function " + pretty_print_function(fnName, fnNamespace, argv) + "\n{", file=sink)
            ip += 3 + 3*1 + 1*argc
            if fnName == "onExplode" and fnNamespace == "ProjectileData":
                ip = fnEndLoc
            elif fnName == "doScreenShot" or fnName == "doHudScreenshot" or fnName == "doDofScreenShot":
                ip = fnEndLoc
        elif opcode == "META_ENDFUNC":
            if in_function:
                in_function = False
                indentation -= 1
            print(indentation*"\t" + "}\n", file=sink)
            del dso.code[ip - 1]  # Delete the metadata we added to avoid desyncing absolute jumps.
            if print_me:
                print_me = 0
                enable_debug = 0
            if not nofolder:
                sink.close()
                sink = varSink
            arguments = []
            ip -= 1
            indentation = 0
        elif opcode == "OP_CALLFUNC_RESOLVE":
            #fnName = dso.get_string(dso.code[ip])
            #fnNamespace = dso.get_string(dso.code[ip + 1])
            #print("fnName " + fnName)
            #print("fnNamespace " + fnNamespace)
            dso.code[ip - 1] = 43
            ip -= 1
        elif opcode == "OP_CALLFUNC":
            fnCallType = CALL_TYPES[dso.code[ip + 2]]
            fnName = dso.get_string(dso.code[ip])
            fnNamespace = dso.code[ip + 1]
            if fnNamespace:
                fnNamespace = dso.get_string(fnNamespace)
            else:
                fnNamespace = ""
            #print("fnName " + fnName)
            #print("fnNamespace " + fnNamespace)
            #print(str(fnCallType))
            if arguments == []:
                arguments = [""]
            try: 
                string_stack.append(pretty_print_function(fnName, fnNamespace, arguments[-1], fnCallType))
            except IndexError:
                print("stuck at " + sink.name)
                print("function stuck " + fnName)
                print("arguments " + str(arguments))
                sys.exit(1)
            arguments.pop()
            if enable_debug:
                try:
                    for i in range(3):
                        print("//" + str(dso.code[ip + i]), file=sink)
                except KeyError:
                    print("//Error!", file=sink)
            ip += 1 + 2*1
        elif opcode == "OP_RETURN":
            #There will always be two returns if it's returning a val.
            if enable_debug:
                print("//RETURN", file=sink)
            if offset != 0:
                if len(string_stack) > 0 and string_stack[-1] != "":
                    print(indentation*"\t" + "return %s;" % string_stack.pop(), file=sink)
                elif ip != len(dso.code) and dso.code[ip] != METADATA["META_ENDFUNC"]:
                    print(indentation*"\t" + "return;", file=sink)
                continue
            try:
                if len(string_stack) > 0 and string_stack[-1] != "" and dso.code[ip] != METADATA["META_ENDFUNC"] and dso.code[ip] != METADATA["META_ENDWHILE"]:
                    if previous_opcodes[0][:12] == "OP_LOADIMMED" or previous_opcodes[0][:12] == "OP_SETCURVAR" or previous_opcodes[0][:11] == "OP_CALLFUNC" or previous_opcodes[0][:10] == "OP_LOADVAR" or previous_opcodes[0][:9] == "OP_REWIND" or previous_opcodes[0][:12] == "OP_LOADFIELD" or previous_opcodes[0][-6:] == "TO_STR":
                        print(indentation*"\t" + "return %s;" % string_stack.pop(), file=sink)
                    else:
                        print(indentation*"\t" + "return;", file=sink)
                elif ip != len(dso.code) and dso.code[ip] != METADATA["META_ENDFUNC"] and previous_opcodes[0][:-4] != "OP_LOADVAR" and dso.code[ip] != METADATA["META_ENDWHILE"]:
                    # Omit the return if the function or the script ends here
                    print(indentation*"\t" + "return;", file=sink)
            except IndexError:
                #If this happens, it's likely we're at the end
                pass

## END OF FUNCTION RELATED FUNCTIONS ##
## START OF OBJ CREATION ##
        elif opcode == "OP_CREATE_OBJECT":
            objParent = dso.get_string(dso.code[ip])
            isDatablock = dso.code[ip + 1]
            failJump = dso.code[ip + 2]
            #print("[object creation]")
            #print("[objParent] " + objParent, file=sink)
            #print("[isDatablock] " + str(isDatablock), file=sink)
            #print("[failJump] " + str(failJump), file=sink)
            #print("[arguments]" + str(arguments[-1]), file=sink)
            argv = arguments[-1]
            newObj = "new %s(%s){\n" % (argv[0], argv[1])
            int_stack.append(newObj)
            in_obj_creation = 1
            indentation += 1
            arguments.pop()
            ip += 3
            #break;
        elif opcode == "OP_END_OBJECT":
            indentation -= 1
            ip += 1
            op = int_stack.pop()
            if op.endswith("\n" + "\t" + "{\n"):  # Empty object declaration, omit body.
                blo = op[:-3-indentation]
                int_stack.append(blo)
            else:
                int_stack.append(op + indentation*"\t" + "};")
            if get_opcode(0, dso.code[ip]) != "OP_UINT_TO_NONE" and get_opcode(0, dso.code[ip]) != "OP_UINT_TO_STR" and get_opcode(0, dso.code[ip]) != "OP_SETCURVAR_CREATE":
                print(int_stack.pop(), file=sink)
            in_obj_creation = 0
            #print(int_stack.pop(), file=sink)
        elif opcode == "OP_SETCUROBJECT":
            current_object = string_stack.pop()
        elif opcode == "OP_SETCUROBJECT_NEW":
            current_object = None
        elif opcode == "OP_ADD_OBJECT":
            ip += 1
            pass
        elif opcode == "OP_SETCURFIELD":
            current_field = dso.get_string(dso.code[ip])
            ip += 1
        
## END OF OBJ CREATION ##                
## START OF PUSH FRAME, PUSH ##
        elif opcode == "OP_PUSH_FRAME":
            arguments.append([])
        elif opcode == "OP_PUSH":
            if previous_opcodes[0][:-4] == "OP_LOADVAR":
                #We want to push this to args!
                if len(arguments) == 0:
                    arguments.append([])
                arguments[-1].append(string_stack.pop())
            elif len(arguments) == 0:
                arguments.append([])
                if enable_debug:
                    print("//insert blank", file=sink)
            else:
                s0 = string_stack.pop()
                arguments[-1].append(s0)
                if enable_debug:
                    print("//" + str(len(arguments)), file=sink)
                    print("//" + str(arguments[-1]), file=sink)
## END OF PUSH FRAME, PUSH ##
## START OF VARIABLE NONSENSE ##
        elif opcode == "OP_SETCURFIELD_ARRAY":
            s1 = string_stack.pop()
            current_field = current_field + ("[%s]" % s1)
            pass
        elif opcode == "OP_SETCURVAR_CREATE" or opcode == "OP_SETCURVAR":
            current_variable = dso.get_string(dso.code[ip])
            if current_variable == "_Timeout":
                current_variable = dso.get_string(dso.code[67931])
            current_variable = current_variable.replace(";", "")# Always lookup in the global ST for this opcode
            ip += 1
        elif opcode == "OP_SETCURVAR_ARRAY" or opcode == "OP_SETCURVAR_ARRAY_CREATE":
            current_variable = string_stack.pop()
        elif opcode == "OP_LOADVAR_STR":
            string_stack.append(current_variable)
        elif opcode == "OP_LOADIMMED_IDENT":
            string_stack.append('%s' % dso.get_string(dso.code[ip]))  # Always pick from the global pool
            if enable_debug:
                print("//LOAD IDENT " + dso.get_string(dso.code[ip]), file=sink)
            ip += 1
## END OF VARIABLE ##
## START OF STRING OPS ##
        elif opcode == "OP_ADVANCE_STR_NUL":
            pass
        elif opcode == "OP_COMPARE_STR":
            op = string_stack.pop()
            int_stack.append("%s $= %s" % (string_stack.pop(), op))
        elif opcode == "OP_STR_TO_NONE":
            if previous_opcodes[0] == "OP_CALLFUNC" or previous_opcodes[0] == "OP_CALLFUNC_RESOLVE" or (previous_opcodes[0] == "META_ENDIF" and (previous_opcodes[1] == "OP_CALLFUNC" or previous_opcodes[1] == "OP_CALLFUNC_RESOLVE")):
                # CALLFUNC -> STR_TO_NONE means ignored return value. Write the call right now, because
                # it won't be assigned to anything.
                s0 = string_stack.pop()
                #print(s0)
                if s0.endswith(";"):
                    print("%s%s" % (indentation*"\t", s0), file=sink)
                else:
                    print("%s%s;" % (indentation*"\t", s0), file=sink)
            else:
                try:
                    string_stack.pop()  # I get some mismatches with the OP_TERMINATE_REWIND_STR opcode family.
                except IndexError:
                    pass
        elif opcode == "OP_STR_TO_FLT":
            float_stack.append(string_stack.pop())
        elif opcode == "OP_LOADIMMED_STR" or opcode == "OP_TAG_TO_STR":
            op = dso.get_string(dso.code[ip], in_function)
            #Weird bug with "amLobbyArg". It's not supposed to be there.
            if op == "amLobbyArg":
                #Probably didn't load correctly.
                op = "lolok"
            ip += 1
            if enable_debug:
                print("//LOAD STR " + op, file=sink)
                print("//AT IP " + str(ip-1), file=sink)
            dso.code[ip - 1] = METADATA["META_SKIP"]
            # Some floats may be represented as string literals. Omit brackets for those.
            if opcode == "OP_TAG_TO_STR":  # Tagged strings are encased in single quotes.
                op = op.replace("'", "")
                string_stack.append('%s' % op if is_number(op) else "'%s'" % op)
            else:
                # Also escape any double quote in the string.
                if op.endswith('"'):
                    op = op[:-1]
                elif op[:1] == '"':
                    op = op.replace('"', "")
                #print(op)
                string_stack.append('%s' % op if is_number(op) else '"%s"' % op.replace('"', '\\"'))
        elif opcode == "OP_ADVANCE_STR":
             pass
             string_stack.insert(0, "")
        elif opcode == "OP_REWIND_STR":
            if get_opcode(dso.version, dso.code[ip]).startswith("OP_SETCURVAR_ARRAY"):  # This is an array access
                s2 = string_stack.pop()
                string_stack.append("%s[%s]" % (string_stack.pop(), s2))
            else:
                s2 = string_stack.pop()
                s1 = string_stack.pop()
                if s1[-1] in STRING_OPERATORS:
                    string_stack.append("%s %s %s" % (s1[:-1], STRING_OPERATORS[s1[-1]], s2))
                elif s1[-1] == ",":  # Matrix indexing
                    string_stack.append("%s%s" % (s1, s2))
                else:
                    string_stack.append("%s @ %s" % (s1, s2))
        elif opcode == "OP_SAVEVAR_STR":
           # print("save var!!", file=sink)
            if string_stack[-1].endswith(";"):
                print(indentation*"\t" + '%s = %s' % (current_variable, string_stack[-1]), file=sink)
            else:
                print(indentation*"\t" + '%s = %s;' % (current_variable, string_stack[-1]), file=sink)
        elif opcode == "OP_TERMINATE_REWIND_STR":
            pass
        elif opcode == "OP_SAVEFIELD_STR":
            #if in_obj_creation:
                #print("save field!!", file=sink)
            if current_object != None:
                if current_object.startswith("%"):
                    print(indentation*"\t" + '%s.%s = %s;' % (current_object, current_field, string_stack[-1]), file=sink)
                else:
                    print(indentation*"\t" + '"%s".%s = %s;' % (current_object, current_field, string_stack[-1]), file=sink)
            else:
                if in_obj_creation:
                    int_stack.append(int_stack.pop() + indentation*"\t" + '%s = %s;\n' % (current_field, string_stack[-1] if string_stack[-1] is not "" else '""'))
                else:
                    print(indentation*"\t" + '%s = %s;' % (current_field, string_stack[-1]), file=sink)
        elif opcode == "OP_LOADFIELD_STR":
            string_stack.append("%s.%s" % (current_object, current_field))
        elif opcode == "OP_STR_TO_UINT":
            int_stack.append(string_stack.pop())
        elif opcode == "OP_ADVANCE_STR_APPENDCHAR":
            c = chr(dso.code[ip])
            string_stack[-1] += c
            ip += 1
        elif opcode == "OP_ADVANCE_STR_COMMA":
            string_stack[-1] += ","

## END OF STRING OPS ##
## START OF UINT OPS ##
        elif opcode == "OP_SAVEVAR_UINT":
            if str(int_stack[-1]).endswith(";"):
                print(indentation*"\t" + "%s = %s" % (current_variable, int_stack[-1]), file=sink)
            else:
                print(indentation*"\t" + "%s = %s;" % (current_variable, int_stack[-1]), file=sink)
        elif opcode == "OP_LOADIMMED_UINT":
            int_stack.append(dso.code[ip])
            ip += 1
        elif opcode == "OP_LOADVAR_UINT":
            int_stack.append(current_variable)
        elif opcode == "OP_LOADFIELD_UINT":
            if current_object.startswith("%"):
                int_stack.append('%s.%s' % (current_object, current_field))
            else:
                int_stack.append('"%s".%s' % (current_object, current_field))
        elif opcode == "OP_UINT_TO_NONE":
            if previous_opcodes[0] == "OP_END_OBJECT":
                #print(int_stack)
                print(indentation*"\t" + int_stack.pop(), file=sink)
            else:
                int_stack.pop()
        elif opcode == "OP_UINT_TO_FLT":
            float_stack.append(int_stack.pop())
        elif opcode == "OP_UINT_TO_STR":
            string_stack.append("("+str(int_stack.pop())+")")
        elif opcode == "OP_LOADVAR_FLT":
            float_stack.append(current_variable)
## END OF UINT OPS ##
## START OF FLT OPS ##
        elif opcode == "OP_SAVEFIELD_FLT":
           # print("saving flt", file=sink)
            if current_object != None:
                if current_object.startswith("%"):
                    print(indentation*"\t" + '%s.%s = %s;' % (current_object, current_field, float_stack[-1]), file=sink)
                else:
                    print(indentation*"\t" + '"%s".%s = %s;' % (current_object, current_field, float_stack[-1]), file=sink)
            else:
                print(indentation*"\t" + '%s = %s;' % (current_field, float_stack[-1]), file=sink)
        elif opcode == "OP_LOADFIELD_FLT":
            if current_object.startswith("%"):
                float_stack.append('%s.%s' % (current_object, current_field))
            else:
                float_stack.append('"%s".%s' % (current_object, current_field))
        elif opcode == "OP_FLT_TO_STR":
            string_stack.append(str(float_stack.pop()))
        elif opcode == "OP_FLT_TO_NONE":
            float_stack.pop()
        elif opcode == "OP_SAVEVAR_FLT":
            print(indentation*"\t" + "%s = %s;" % (current_variable, float_stack[-1]), file=sink)
        elif opcode == "OP_FLT_TO_UINT":
            int_stack.append("("+str(float_stack.pop())+")")
        elif opcode == "OP_LOADIMMED_FLT":
            float_stack.append(dso.get_float(dso.code[ip], in_function))
            ip += 1
## END OF FLT OPS ##
## START OF LOGICAL/MATH OPS ##
        elif opcode == "OP_CMPEQ" or \
             opcode == "OP_CMPLT" or \
             opcode == "OP_CMPNE" or \
             opcode == "OP_CMPGR" or \
             opcode == "OP_CMPGE" or \
             opcode == "OP_CMPLE":
            op1 = float_stack.pop()
            op2 = float_stack.pop()
            op1 = "%s %s %s" % (str(op1), COMPARISON[opcode], str(op2))
            int_stack.append(op1)
        elif opcode == "OP_BITAND":
            op1 = int_stack.pop()
            op2 = int_stack.pop()
            op1 = "%s & %s" % (str(op1), str(op2))
            int_stack.append(op1)
        elif opcode == "OP_BITOR":
            #print(int_stack)
            op1 = int_stack.pop()
            op2 = int_stack.pop()
            op1 = "%s | %s" % (str(op1), str(op2))
            int_stack.append(op1)
            #print(ip)
            #break
        elif opcode == "OP_SHL":
            op1 = int_stack.pop()
            op2 = int_stack.pop()
            op1 = "%s << %s" % (str(op1), str(op2))
            int_stack.append(op1)
            #print(op1)
        elif opcode == "OP_NOT":
            op1 = str(int_stack.pop())
            if op1.count("==") == 1:
                int_stack.append(op1.replace("==", "!="))
            elif op1.count("!=") == 1:
                int_stack.append(op1.replace("!=", "=="))
            elif op1.count("$=") == 1:
                int_stack.append(op1.replace("$=", "!$="))
            elif op1.count("!$=") == 1:
                int_stack.append(op1.replace("!$=", "$="))
            elif not op1.startswith("!"):
                int_stack.append("!%s" % op1)
            elif " " in op1:
                int_stack.append("!(%s)" % op1)  # Encase in parentheses if this is a compound operation
            else:
                int_stack.append(op1[1:])  # Avoid "!!" in front of variables
        elif opcode == "OP_NOTF":
            if print_me:
                #debug!
                try:
                    print(get_opcode(0, dso.code[ip]), file=sink)
                except KeyError:
                    pass

            op1 = float_stack.pop()
            if isinstance(op1, str):
                if not op1.startswith("!"):
                    int_stack.append("!%s" % op1)
                else:
                    int_stack.append(op1[1:])  # Avoid "!!" in front of variables
            else:  # The VM replaces true and false with 0 and 1.
                int_stack.append("false" if float(op1) == 0 else "true")
        elif opcode == "OP_MUL":
            op1 = float_stack.pop()
            if isinstance(op1, str) and (' + ' in op1 or " - " in op1):
                op1 = "(%s)" % op1  # operand is the result of an add/sub, prevent priority issues.
            float_stack.append("%s * %s" % (op1, float_stack.pop()))
        elif opcode == "OP_DIV":
            op1 = float_stack.pop()
            if isinstance(op1, str) and ('+' in op1 or " -" in op1):
                op1 = "(%s)" % op1  # operand is the result of an add/sub, prevent priority issues.
            if len(float_stack) > 0:
                float_stack.append("%s / %s" % (op1, float_stack.pop()))
            else:
                float_stack.append("%s / %s" % (op1, string_stack.pop()))
        elif opcode == "OP_ADD":
            float_stack.append("%s + %s" % (float_stack.pop(), float_stack.pop()))
        elif opcode == "OP_SUB":
            float_stack.append("%s - %s" % (float_stack.pop(), float_stack.pop()))
        elif opcode == "OP_IGNORE":
            pass
        elif opcode == "OP_NEG":
            if enable_debug:
                print("//" + str(float_stack[-1]), file=sink)
                print("//" + str(type(float_stack[-1])), file=sink)
            op1 = float_stack.pop()
            if type(op1) is not str:
                float_stack.append(-1 * op1)
            else:
                if op1.startswith("-"):
                    float_stack.append(op1[1:])
                else:
                    float_stack.append("(-%s)" % op1)
        elif opcode == "OP_MOD":
            op = int_stack.pop()
            int_stack.append("%s %% %s" % (int_stack.pop(), op))
## END OF LOGICAL/MATH OPS ##
## START OF JMP OPS ##
        elif opcode == "OP_JMP":
            # Normally, these opcode should only be encountered because of the "break" keyword.
            jmp_target = dso.code[ip - 2]
            #print(dso.code[jmp_target])
            dso.code[jmp_target - 2] == "META_ENDWHILE";
            print(indentation*"\t" + "break;", file=sink)
            ip += 1
        elif opcode == "OP_JMPIF":
            ip += 1
            pass
        elif opcode == "OP_JMPIF_NP":
            binary_stack.append(int_stack.pop() + " || ")
            jmp_target = dso.code[ip] - offset
            dso.code.insert(jmp_target, METADATA["META_END_BINARYOP"])
            ip += 1
        elif opcode == "OP_JMPIFNOT_NP":
            binary_stack.append(int_stack.pop() + " && ")
            jmp_target = dso.code[ip] - offset
            dso.code.insert(jmp_target, METADATA["META_END_BINARYOP"])
            ip += 1
        elif opcode == "OP_JMPIFNOT" or opcode == "OP_JMPIFFNOT":
            # We need to determine the type of branch we're facing. The opcode just before the jump destination
            # gives us hints.
            jmp_target = dso.code[ip] - offset
            if jmp_target < ip:
                print("Error: unexpected backward jump.", file=sys.stderr)
                sys.exit(1)
            elif jmp_target == ip + 1:  # If statement with an empty body. Simply skip it.
                ip += 1
                if opcode == "OP_JMPIFNOT":
                    int_stack.pop()
                elif opcode == "OP_JMPIFFNOT":
                    float_stack.pop()
                continue
            try:
                opcode_before_dest = get_opcode(dso.version, dso.code[jmp_target - 2])
            except KeyError:
                if enable_debug:
                    print("//KeyError encountered", file=sink)
                opcode_before_dest = get_opcode(dso.version, dso.code[jmp_target - 1])
            if enable_debug:
                print("//JMP TO " + str(jmp_target), file=sink)
                print("//CUR IP " + str(ip), file=sink)
            # Probably ambiguous :(
            if opcode_before_dest == "OP_JMP":  # If-then-else construction or ternary operator
                # Test if this is a ternary expression, i.e (a ? b : c)
                if dso.code[jmp_target - 4] == jmp_target:
                    opcode_before_jmp = "OP_IGNORE"
                else:
                    try:
                        opcode_before_jmp = get_opcode(dso.version, dso.code[jmp_target - 4])
                    except KeyError:
                        opcode_before_jmp = "OP_IGNORE"
                if opcode_before_jmp and opcode_before_jmp.startswith("OP_LOADIMMED"):
                    # The loop ends with something being pushed on a stack. This is a ternary operator.
                    dso.code[jmp_target - 2] = METADATA["META_ELSE"]
                    # Obtain the stacks after evaluating the expression:
                    s_s, i_s, f_s = partial_decompile(dso, ip+1, dso.code[jmp_target - 1], in_function)
                    if len(s_s) == 2:
                        op1 = s_s.pop()
                        string_stack.append("(%s) ? %s : %s" % (int_stack.pop() if opcode == "OP_JMPIFNOT" else float_stack.pop(),
                                                              s_s.pop(),
                                                              op1))
                        ip = dso.code[jmp_target - 1] # Skip past the construction
                        continue
                    elif len(i_s) == 2:
                        op1 = i_s.pop()
                        int_stack.append("(%s) ? %s : %s" % (int_stack.pop() if opcode == "OP_JMPIFNOT" else float_stack.pop(),
                                                           i_s.pop(),
                                                           op1))
                        ip = dso.code[jmp_target - 1]
                        continue
                    elif len(f_s) == 2:
                        op1 = f_s.pop()
                        float_stack.append("(%s) ? %s : %s" % (int_stack.pop() if opcode == "OP_JMPIFNOT" else float_stack.pop(),
                                                             f_s.pop(),
                                                             op1))
                        ip = dso.code[jmp_target - 1]
                        continue
                    # If this point is reached, this may not have been a ternary operator after all. Continue as if
                    # it was an if-then-else.
                # If-then-else
                if opcode == "OP_JMPIFNOT":
                    print(indentation*"\t" + "if (%s)" % int_stack.pop() + "\n" + indentation*"\t" + "{", file=sink)
                elif opcode == "OP_JMPIFFNOT":
                    print(indentation*"\t" + "if (%s)" % float_stack.pop() + "\n" + indentation*"\t" + "{", file=sink)
                # Annotate code
                if enable_debug:
                    print("//A", file=sink)
                dso.code[jmp_target - 2] = METADATA["META_ELSE"]
                dso.code.insert(dso.code[jmp_target - 1], METADATA["META_ENDIF"])
            elif opcode_before_dest == "OP_JMPIFNOT" or opcode_before_dest == "OP_JMPIF":  # For/While loop
                ind = indentation*"\t"
                # This may be an easy while loop:
                if get_opcode(dso.version, dso.code[jmp_target - 3]) == "OP_NOTF":
                    print(ind + "while(%s)\n" % int_stack.pop() + ind + "{", file=sink)
                else:
                    print(ind + "while(%s)\n" % (int_stack.pop()) + ind + "{", file=sink)
                try:
                    blo = get_opcode(0, dso.code[jmp_target - 2])
                    if enable_debug:
                        print("//passed " + blo, file=sink)
                        print("//jmp trgt " + str(jmp_target), file=sink)
                    bb = get_opcode(0, dso.code[jmp_target])
                    if bb == "OP_PUSH_FRAME" or get_opcode(0, dso.code[jmp_target - 3]) == "OP_LOADIMMED_STR":
                        dso.code.insert(jmp_target, METADATA["META_ENDWHILEB"])
                    elif blo[:8] == "OP_JMPIF":
                        dso.code[jmp_target - 2] = METADATA["META_ENDWHILE"]
                    #It should never pass.
                except KeyError:
                    dso.code[jmp_target - 2] = METADATA["META_ENDWHILE"]
            elif opcode_before_dest == "OP_JMPIFF":  # While loop
                ind = indentation*"\t"
                print(ind + "while(%s)\n" % float_stack.pop() + ind + "{", file=sink)
                dso.code[jmp_target - 2] = METADATA["META_ENDWHILE_FLT"]
            else:
                # Generic opcode before the jump target. We assume that the execution is continuing and
                # that this is therefore a simple If control structure.
                if opcode == "OP_JMPIFNOT":
                    print(indentation*"\t" + "if (%s)" % int_stack.pop() + "\n" + indentation*"\t" + "{", file=sink)
                elif opcode == "OP_JMPIFFNOT":
                    print(indentation*"\t" + "if (%s)" % float_stack.pop() + "\n" + indentation*"\t" + "{", file=sink)
                if enable_debug:
                    print("//B", file=sink)
                dso.code.insert(jmp_target, METADATA["META_ENDIF"])
            ip += 1
            indentation += 1

## END OF JMP OPS ##
## START OF META OPS ##
        elif opcode == "OP_IGNORE":
            pass
        elif opcode == "META_END_BINARYOP":
            if get_opcode(0, dso.code[ip - 1]) == "META_END_BINARYOP":
                del dso.code[ip - 1]  # Delete the metadata we added to avoid desyncing absolute jumps.
            ip -= 1
            op1 = binary_stack.pop()
            if len(int_stack) > 0:
                op2 = int_stack.pop()
            elif len(float_stack) > 0:
                op2 = float_stack.pop()
            elif len(string_stack) > 0:
                op2 = string_stack.pop()
            op2 = str(op2)
            if "&&" in op2 or "||" in op2:
                op2 = "(%s)" % op2
            int_stack.append("%s%s" % (op1, op2))
        elif opcode == "META_ELSE":
            ind = (indentation-1)*"\t"
            print(ind + "}\n" + ind + "else\n" + ind + "{", file=sink)
            ip += 1  # META_ELSE replaces an existing opcode so there it doesn't cause problems - no need to del it
        elif opcode == "META_ENDIF" or opcode == "META_ENDWHILE_FLT" or opcode == "META_ENDWHILE" or opcode == "META_ENDWHILEB":
            indentation -= 1
            print(indentation*"\t" + "}", file=sink)
            if opcode == "META_ENDIF":
                del dso.code[ip - 1]
                ip -= 1
                if offset == 0:
                    try:
                        get_opcode(0, dso.code[ip])
                    except KeyError:
                        ip += 1
            elif opcode == "META_ENDWHILE_FLT":
                ip += 1
                float_stack.pop()  # A test condition will have been pushed and needs to be cleaned.
            elif opcode == "META_ENDWHILE":
                ip += 1
                int_stack.pop()  # A test condition will have been pushed and needs to be cleaned.
            elif opcode == "META_ENDWHILEB":
                del dso.code[ip - 1]
                ip -= 1
## END OF META OPS ##
## EOF HERE ##
        else:
            print("%s not implemented yet. Stopped at ip=%d." % (opcode, ip), file=sys.stderr)
            sys.exit(1)

        previous_opcodes.pop()
        previous_opcodes.insert(0, opcode)

    return string_stack, int_stack, float_stack




