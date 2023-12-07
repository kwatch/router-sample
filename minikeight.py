# -*- coding: utf-8 -*-

import sys, re, json
from datetime import date
from wsgiref.util import setup_testing_defaults

PY3 = sys.version_info[0] == 3
if not PY3:
    raise Exception("supports only Python3.")


class RouterError(Exception):
    pass


class Router(object):

    def find(self, req_path):
        raise NotImplementedError("%s.find(): not implemented yet." % self.__class__.__name__)

    def lookup(self, req_meth, req_path):
        t = self.find(req_path)
        if t is None:
            return None, None, None
        handler_class, handler_methods, param_args = t
        fn = handler_methods.get
        handler_func = fn(req_meth) or (req_meth == 'HEAD' and fn('GET')) or fn('ANY')
        return handler_class, handler_func, param_args  # handler_func may be None

    def _traverse(self, mapping, root_path):
        for base_path, arg in mapping:
            if isinstance(arg, list):
                child_mapping = arg
                yield from self._traverse(child_mapping, root_path+base_path)
            else:
                handler_class = arg
                self._validate(handler_class)
                for path, handler_methods in handler_class.__mapping__:
                    full_path_pat = root_path+base_path+path
                    yield full_path_pat, handler_class, handler_methods

    def _validate(self, handler_class):
        cls = handler_class
        if type(cls) is not type:
            raise RouterError("%s: handler class expected." % (cls,))
        if not issubclass(cls, RequestHandler):
            raise RouterError("%s: should be a subclass of RequestHandler." % (cls,))
        if getattr(cls, '__mapping__', None) is None:
            raise RouterError("%s: no handler funcs defined." % (cls,))

    def _scan(self, urlpath_pattern):
        m1 = None
        for m1 in re.finditer(r'(.*?)\{([^}]*)\}', urlpath_pattern):
            text, placeholder = m1.groups()
            #m2 = re.match(r'^(\w+)(:\w+)?(<.*>)?$', placeholder)
            m2 = re.match(r'^(\w+)(:\w+)?$', placeholder)
            if not m2:
                raise RouterError("%s: invalid placeholder (expected '{name:type<rexp>})'" % urlpath_pattern)
            pname, ptype = m2.groups()
            ptype = ptype[1:] if ptype else 'str'
            tupl = self.URLPATH_PARAM_TYPES.get(ptype, None)
            if tupl is None:
                raise RouterError("%s: unknown param type '%s'." % (urlpath_pattern, ptype))
            prexp, pfunc = tupl
            yield text, pname, ptype, prexp, pfunc
        text = (urlpath_pattern[m1.end():] if m1 else
                urlpath_pattern)
        if text:
            yield text, None, None, None, None

    def _compile(self, urlpath_pattern, begin='^', end='$', grouping=True):
        if urlpath_pattern.endswith('.*'):
            end = r'(?:\.\w+)?' + end
            urlpath_pattern = urlpath_pattern[:-2]
        arr = [begin]
        param_names = []
        param_funcs = []
        m1 = None
        for text, pname, _ptype, prexp, pfunc, in self._scan(urlpath_pattern):
            if text:
                arr.append(self._escape(text))
            if not pname:
                continue
            if pname in param_names:
                raise RouterError("%s: parameter name '%s' duplicated." % (urlpath_pattern, pname))
            param_names.append(pname)
            param_funcs.append(pfunc)
            if grouping:
                arr.extend((r'(', prexp, r')'))
            else:
                arr.append(prexp)
        arr.append(end)
        return re.compile("".join(arr)), param_names, param_funcs

    def _date(s):
        try:
            yr, mo, dy = s.split('-')
            return date(int(yr), int(mo), int(dy))
        except:
            return None

    URLPATH_PARAM_TYPES = {
        'int'  : (r'\d+'   , int),
        'str'  : (r'[^./]+', None),
        'date' : (r'\d\d\d\d-\d\d-\d\d', _date),
        'path' : (r'.*'    , None),
    }
    del _date

    def _escape(self, s, _fn=lambda m: '\\'+m.group(0)):
        return re.sub(r'[.*+?^$|\[\]{}()]', _fn, s)


class NaiveLinearRouter(Router):
    """Linear (naive)"""

    def __init__(self, mapping):
        self._mapping_list = []
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            path_rexp, param_names, param_funcs = self._compile(path_pat)
            t = (path_pat, path_rexp,
                 handler_class, handler_methods, param_names, param_funcs)
            self._mapping_list.append(t)

    def find(self, req_path):
        for t in self._mapping_list:
            _, path_rexp, handler_class, handler_methods, _, param_funcs = t
            m = path_rexp.match(req_path)
            if m:
                param_args = [ (f(s) if f is not None else s)
                                   for s, f in zip(m.groups(), param_funcs) ]
                return handler_class, handler_methods, param_args
        return None


class PrefixLinearRouter(Router):
    """Linear (prefixstr)"""

    def __init__(self, mapping):
        self._mapping_list = []
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            path_rexp, param_names, param_funcs = self._compile(path_pat)
            path_prefix = path_pat.split('{', 1)[0]
            t = (path_pat, path_prefix, path_rexp,
                 handler_class, handler_methods, param_names, param_funcs)
            self._mapping_list.append(t)

    def find(self, req_path):
        for t in self._mapping_list:
            _, path_prefix, path_rexp, handler_class, handler_methods, _, param_funcs = t
            if not req_path.startswith(path_prefix):
                continue
            m = path_rexp.match(req_path)
            if m:
                param_args = [ (f(s) if f is not None else s)
                                   for s, f in zip(m.groups(), param_funcs) ]
                return handler_class, handler_methods, param_args
        return None


class FixedLinearRouter(Router):
    """Linear (fixedpath)"""

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._mapping_list = []   # for urlpath having no parameters
        append = self._mapping_list.append
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                path_prefix = path_pat.split('{', 1)[0]
                path_rexp, param_names, param_funcs = self._compile(path_pat)
                t = (path_pat, path_prefix, path_rexp,
                     handler_class, handler_methods, param_names, param_funcs)
                self._mapping_list.append(t)

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        for t in self._mapping_list:
            _, path_prefix, path_rexp, handler_class, handler_methods, _, param_funcs = t
            if not req_path.startswith(path_prefix):
                continue
            m = path_rexp.match(req_path)
            if m:
                param_args = [ (f(s) if f is not None else s)
                                   for s, f in zip(m.groups(), param_funcs) ]
                return handler_class, handler_methods, param_args
        return None


class NaiveRegexpRouter(Router):
    """Regexp (naive)"""

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._mapping_list = []   # for urlpath having no parameters
        all = []; i = 0; pos = 0
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                path_rexp, param_names, param_funcs = self._compile(path_pat)
                t = (path_pat, pos + 1, len(param_names),
                     handler_class, handler_methods, param_names, param_funcs)
                self._mapping_list.append(t)
                all.append("(?P<_%s>%s)" % (i, path_rexp.pattern))
                i += 1; pos += 1 + len(param_names)
        self._all_regexp = re.compile("|".join(all))

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        if not self._mapping_list:
            return None
        m = self._all_regexp.match(req_path)
        if m is None:
            return None
        for k, v in m.groupdict().items():
            if v:
                i = int(k[1:])
                break
        else:
            assert false, "unreachable"
        t = self._mapping_list[i]
        _, pos, n, handler_class, handler_methods, _, param_funcs = t
        params = m.groups()[pos:pos+n]
        param_args = [ (f(s) if f is not None else s)
                           for s, f in zip(params, param_funcs) ]
        return handler_class, handler_methods, param_args


class SmartRegexpRouter(Router):
    """Regexp (smart)"""

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._mapping_list = []   # for urlpath having no parameters
        all = []
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                path_rexp, param_names, param_funcs = self._compile(path_pat)
                t = (path_pat, path_rexp,
                     handler_class, handler_methods, param_names, param_funcs)
                self._mapping_list.append(t)
                ## ex: '^/books/([^./]+)$' -> '^/books/(?:[^./]+)($)'
                pattern = self._compile(path_pat, '^', '($)', False)[0].pattern
                all.append(pattern)
        self._all_regexp = re.compile("|".join(all))

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        if not self._mapping_list:
            return None
        m = self._all_regexp.match(req_path)
        if m is None:
            return None
        idx = m.groups().index("")  # ex: m.groups() == [None, None, "", None]
        _, path_rexp, handler_class, handler_methods, _, param_funcs = self._mapping_list[idx]
        m2 = path_rexp.match(req_path)
        param_args = [ (f(s) if f is not None else s)
                           for s, f in zip(m2.groups(), param_funcs) ]
        return handler_class, handler_methods, param_args


class NestedRegexpRouter(Router):
    """Regexp (nested)"""

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._mapping_list = []   # for urlpath having no parameters
        all = []
        for tupl in self._traverse(mapping, "", all):
            path_pat, handler_class, handler_methods = tupl
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                path_rexp, param_names, param_funcs = self._compile(path_pat)
                t = (path_pat, path_rexp,
                     handler_class, handler_methods, param_names, param_funcs)
                self._mapping_list.append(t)
        self._all_regexp = re.compile("^(?:%s)" % "|".join(all))

    def _traverse(self, mapping, root_path, arr):
        for base_path, arg in mapping:
            arr2 = []
            if isinstance(arg, list):
                child_mapping = arg
                yield from self._traverse(child_mapping, root_path+base_path, arr2)
            else:
                handler_class = arg
                self._validate(handler_class)
                for path, handler_methods in handler_class.__mapping__:
                    full_path_pat = root_path+base_path+path
                    yield full_path_pat, handler_class, handler_methods
                    if '{' not in full_path_pat:
                        continue
                    ## ex: '/([^./]+)' -> '/(?:[^./]+)($)'
                    pattern = self._compile(path, '', '', False)[0].pattern
                    arr2.append(pattern+'($)')
            if not arr2:
                continue
            base_pattern = self._compile(base_path, '', '', False)[0].pattern
            if len(arr2) == 1:
                arr.append("%s%s" % (base_pattern, arr2[0]))
            else:
                arr.append("%s(?:%s)" % (base_pattern, "|".join(arr2)))

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        if not self._mapping_list:
            return None
        m = self._all_regexp.match(req_path)
        if m is None:
            return None
        idx = m.groups().index("")  # ex: m.groups() == [None, None, "", None]
        _, path_rexp, handler_class, handler_methods, _, param_funcs = self._mapping_list[idx]
        m2 = path_rexp.match(req_path)
        param_args = [ (f(s) if f is not None else s)
                           for s, f in zip(m2.groups(), param_funcs) ]
        return handler_class, handler_methods, param_args


class OptimizedRegexpRouter(Router):
    """Regexp (optimized)"""

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._mapping_list = []   # for urlpath having no parameters
        tuples = []
        for tupl in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = tupl
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                tuples.append(tupl)
        tree = self._build_tree(tuples)
        callback = self._mapping_list.append
        self._all_regexp = self._build_rexp(tree, callback)

    def _build_tree(self, tuples):
        tree = []          # tuple list
        for t in tuples:
            urlpath_pattern, handler_class, handler_methods = t
            if urlpath_pattern.endswith('.*'):
                path_pat = urlpath_pattern[:-2]
                suffix_rexp = r'(?:\.\w+)?'
            else:
                path_pat = urlpath_pattern
                suffix_rexp = None
            param_names = []
            param_funcs = []
            node = tree
            sb = [r'^']
            for text, pname, _ptype, prexp, pfunc in self._scan(path_pat):
                if text:
                    sb.append(self._escape(text))
                    node2 = self._next_node(node, text)
                    node = node2
                if not pname:
                    continue
                if pname in param_names:
                    raise RouterError("%s: parameter name '%s' duplicated." % (urlpath_pattern, pname))
                param_names.append(pname)
                param_funcs.append(pfunc)
                sb.extend((r'(', prexp, r')'))
                node = self._next_node(node, (prexp,))
            if suffix_rexp:
                sb.append(suffix_rexp)
                node = self._next_node(node, (suffix_rexp,))
            sb.append(r'$')
            urlpath_rexp = re.compile("".join(sb))
            tuple = (urlpath_pattern, urlpath_rexp,
                     handler_class, handler_methods,
                     param_names, param_funcs)
            for pair in node:
                assert pair[0] is None, "** internal error: pair[1]=%r" % (pair[1])
            node.append((None, tuple))
        return tree

    def _next_node(self, node, key):
        for i, (k, v) in enumerate(node):
            if isinstance(k, str):
                if isinstance(key, str) and k[0] == key[0]:
                    prefix, rest1, rest2 = self._common_prefix(k, key)
                    if not rest1 and not rest2:
                        node2 = v
                    elif not rest1:
                        node2 = self._next_node(v, rest2)
                    elif not rest2:
                        node2 = [(rest1, v)]
                        node[i] = (prefix, node2)
                    else:
                        node2 = []
                        node[i] = (prefix, [(rest1, v), (rest2, node2)])
                    return node2
            elif isinstance(k, tuple):
                if isinstance(key, tuple) and k == key:
                    node2 = v
                    return node2
            elif k is None:
                pass
            else:
                assert False, "** internal error: k=%r" % (k,)
        node2 = []
        node.append((key, node2))
        return node2

    def _common_prefix(self, str1, str2):
        n = min(len(str1), len(str2))
        for i in range(n):
            if str1[i] != str2[i]:
                break
        else:
            i += 1
        prefix = str1[0:i]
        rest1  = str1[i:]
        rest2  = str2[i:]
        return prefix, rest1, rest2

    def _build_rexp(self, tree, callback=None):
        sb = [r'^']
        self.__build_rexp(tree, sb, callback)
        sb.append(r'$')
        return re.compile("".join(sb))

    def __build_rexp(self, node, sb, callback):
        if len(node) > 1:
            sb.append(r'(?:')
        i = 0
        for pair in node:
            k, v = pair
            if i > 0:
                sb.append(r'|')
            i += 1
            if k is None:
                sb.append(r'($)')
                if callback:
                    callback(v)
            elif isinstance(k, str):
                text = k
                sb.append(self._escape(text))
                self.__build_rexp(v, sb, callback)
            elif isinstance(k, tuple):
                prexp = k[0]
                sb.append(prexp)
                self.__build_rexp(v, sb, callback)
            else:
                assert False, "** internal error: k=%r" % (k,)
        if len(node) > 1:
            sb.append(r')')

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        if not self._mapping_list:
            return None
        m = self._all_regexp.match(req_path)
        if m is None:
            return None
        idx = m.groups().index("")  # ex: m.groups() == [None, None, "", None]
        _, path_rexp, handler_class, handler_methods, _, param_funcs = self._mapping_list[idx]
        m2 = path_rexp.match(req_path)
        param_args = [ (f(s) if f is not None else s)
                           for s, f in zip(m2.groups(), param_funcs) ]
        return handler_class, handler_methods, param_args


class SlicedRegexpRouter(OptimizedRegexpRouter):

    def __init__(self, mapping):
        OptimizedRegexpRouter.__init__(self, mapping)
        new_list = []
        for t in self._mapping_list:
            urlpath_pattern, _, _, _, param_names, _ = t
            slice_ = self._slice(urlpath_pattern, param_names)
            new_list.append(t + (slice_,))
        self._mapping_list = new_list

    def _slice(self, urlpath_pattern, param_names):
        if len(param_names) != 1:
            return None
        if urlpath_pattern.endswith('.*'):
            return None
        l_idx = urlpath_pattern.index('{')
        r_idx = urlpath_pattern.rindex('}')
        return slice(l_idx, (r_idx - len(urlpath_pattern) + 1) or None)

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        if not self._mapping_list:
            return None
        m = self._all_regexp.match(req_path)
        if m is None:
            return None
        idx = m.groups().index("")  # ex: m.groups() == [None, None, "", None]
        _, path_rexp, handler_class, handler_methods, _, param_funcs, slice_ = self._mapping_list[idx]
        if slice_ is not None:
            s = req_path[slice_]
            f = param_funcs[0]
            param_args = [f(s) if f is not None else s]
        else:
            m2 = path_rexp.match(req_path)
            param_args = [ (f(s) if f is not None else s)
                               for s, f in zip(m2.groups(), param_funcs) ]
        return handler_class, handler_methods, param_args


class HashedRegexpRouter(Router):
    """Regexp (hashed)"""

    #SUBROUTER_CLASS = OptimizedRegexpRouter
    SUBROUTER_CLASS = SlicedRegexpRouter

    def __init__(self, mapping, prefix_minlength_target=re.compile(r'^/\w')):
        self._mapping_dict = {}   # for urlpath having parameters
        self._subrouters   = {}   # {prefix: OptimizedRegexpRouter}
        #
        x = prefix_minlength_target
        rexp = (re.compile(r'.') if x is None else
                re.compile(x)    if isinstance(x, str) else
                x)
        #
        pairs = [ tupl for tupl in self._traverse(mapping, "") ]
        prefixes = ( p[0].split('{')[0] for p in pairs if rexp.search(p[0]) )
        minlen = min( len(s) for s in prefixes ) or 0
        self._prefix_minlength = minlen
        #
        groups = {}
        for pair in pairs:
            prefix = pair[0][:minlen]
            if prefix.find('{') >= 0 or len(prefix) < minlen:
                prefix = ""
            pairs_ = groups.setdefault(prefix, [])
            pairs_.append(pair)
        #
        for prefix, pairs_ in groups.items():
            subrouter = self.SUBROUTER_CLASS(pairs_)
            self._mapping_dict.update(subrouter._mapping_dict)
            subrouter._mapping_dict.clear()
            self._subrouters[prefix] = subrouter

    def _traverse(self, mapping, base_path="", mapping_class=None):
        if mapping_class is None:
            mapping_class = type(mapping)
        for sub_path, obj in mapping:
            full_path = base_path + sub_path
            if type(obj) is mapping_class:
                yield from self._traverse(obj, full_path, mapping_class)
            else:
                yield full_path, obj

    def find(self, req_path):
        tupl = self._mapping_dict.get(req_path)
        if tupl:
            return tupl  # ex: (BooksAPI, {'GET':do_index, 'POST':do_create}, [])
        prefix = req_path[:self._prefix_minlength]
        subrouter = self._subrouters.get(prefix)
        if subrouter is not None:
            tupl = subrouter.find(req_path)
            if tupl is not None:
                return tupl
        subrouter = self._subrouters.get("")
        if subrouter is not None:
            return subrouter.find(req_path)
        return None


class StateMachineRouter(Router):
    """StateMachine"""

    def _date(s):
        a = s.split('-')
        if len(a) != 3:
            return None
        yr, mo, dy = a
        try:
            return date(int(yr), int(mo), int(dy))
        except:
            return None
    URLPATH_PARAM_TYPES = [
        ('int'  , lambda s: (int(s) if s.isdigit() else None)),
        ('date' , _date),
        ('str'  , lambda s: s or None),
        #('path' , lambda s: s),
    ]
    del _date

    def __init__(self, mapping):
        self._mapping_dict = {}   # for urlpath having parameters
        self._transition   = {}   # for urlpath having no parameters
        ptypes = self.URLPATH_PARAM_TYPES
        self._pkeys = { t[0]: i for i, t in enumerate(ptypes) }  # ex: {'int': 0, 'date': 1, 'str': 2}
        self._pfuncs = [ t[1] for t in ptypes ]  # list of converter func
        for t in self._traverse(mapping, ""):
            path_pat, handler_class, handler_methods = t
            if '{' not in path_pat:
                self._mapping_dict[path_pat] = (handler_class, handler_methods, [])
            else:
                self._register(path_pat, handler_class, handler_methods)

    def _register(self, path_pat, handler_class, handler_methods):
        items, suffix = self._split(path_pat)
        pnames = []
        pkeys = self._pkeys
        d = self._transition
        for item in items:
            if item and item[0] == '{' and item[-1] == '}':
                pair = item[1:-1].split(':', 1)
                pname = pair[0]
                ptype = len(pair) == 2 and pair[1] or 'str'
                if ptype not in pkeys:
                    raise RouterError("%s: unknown parameter type %r." % (path_pat, ptype))
                key = pkeys[ptype]  # ex: 0 (int), 1 (date), 2 (str), 3 (path)
            else:
                key = item
            if key not in d:
                d[key] = {}
            d = d[key]
        if None in d:
            raise RouterError("%s: duplicated urlpath in %s and %s." %
                              (path_pat, d[None][1].__name__, handler_class.__name__))
        d[None] = (suffix, handler_class, handler_methods, pnames)

    def _split(self, path):
        assert path.startswith('/') or not path, "** path=%r" % (path,)
        items = path[1:].split('/')
        basename = items[-1]
        pos = basename.rfind('.')
        if pos >= 0:
            suffix = basename[pos:]
            items[-1] = basename[:pos]
        else:
            suffix = None
        return items, suffix

    def find(self, req_path):
        t = self._mapping_dict.get(req_path)
        if t:
            return t
        #
        items, suffix = self._split(req_path)
        pfuncs = self._pfuncs
        d = self._transition
        param_args = []
        for item in items:
            d2 = d.get(item)
            if d2 is not None:
                d = d2
                continue
            #
            for i, pfunc in enumerate(pfuncs):
                d2 = d.get(i)
                if d2 is not None:
                    v = pfunc(item)
                    if v is not None:
                        param_args.append(v)
                        break
            else:
                return None
            d = d2
        #
        t = d.get(None)
        if t is None:
            return None
        expected_suffix, handler_class, handler_methods, param_names = t
        if not self._valid_suffix(suffix, expected_suffix):
            return None
        return handler_class, handler_methods, param_args

    def _valid_suffix(self, actual_suffix, expected_suffix):
        if actual_suffix == expected_suffix:
            return True
        if expected_suffix == '.*':
            return True
        return False


class RequestHandler(object):

    def __init__(self, req, resp):
        self.req  = req
        self.resp = resp

    def before_request(self):
        pass

    def after_request(self, ex):
        pass

    def handle_request(self, handler_func, param_args):
        ex = None
        try:
            self.before_request()
            content = handler_func(self, *param_args)
            return content
        except Exception as ex_:
            ex = ex_
            raise
        finally:
            self.after_request(ex)


class On(object):

    def __init__(self):
        self._path    = None
        self._actions = None

    def __enter__(self):
        if self._path is None:
            raise RouterError("with on(): unexpected usage.")
        self._actions = {}
        return self

    def __exit__(self, *args):
        frame = sys._getframe(1)
        tuples = frame.f_locals.setdefault('__mapping__', [] )
        tuples.append((self._path, self._actions))
        self._path = None
        self._actions = None

    def path(self, path_pat):
        if self._path:
            raise RouterError("%s: don't nest mapping!" % self._path_pat)
        self._path = path_pat
        return self

    _normalize_rexp = re.compile(r'\{[^}]*\}')

    def __call__(self, meth):
        if meth.upper() != meth:
            raise RouterError("@on('%s'): request method should be upper case." % meth)
        elif meth == 'HEAD':
            raise RouterError("@on('%s'): use 'GET' instead of 'HEAD'." % meth)
        elif not (meth in HTTP_REQUEST_METHODS or meth == 'ANY'):
            raise RouterError("@on('%s'): unknown request method." % meth)
        elif meth in self._actions:
            raise RouterError("@on('%s'): duplicated request method." % meth)
        def deco(func):
            self._actions[meth] = func
            return func
        return deco


on = On()

HTTP_REQUEST_METHODS = {
    'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS', 'TRACE',
}


class Request(object):

    def __init__(self, env):
        self.env = env
        self.method = env['REQUEST_METHOD']
        self.path   = env['PATH_INFO']
        self.query_string = env['QUERY_STRING']

    def header(self, name):
        key = "HTTP_" + name
        return self.env.get(key)

    @property
    def content_type(self):
        return self.env.get('CONTENT_TYPE', None)

    @property
    def content_length(self):
        s = self.env.get('CONTENT_LENGTH', None)
        return int(s) if s is not None else None

    def query(self):
        raise NotImplementedError("%s.query(): not implemented yet." % self.__class__.__name__)

    def form(self):
        raise NotImplementedError("%s.form(): not implemented yet." % self.__class__.__name__)

    def json(self):
        raise NotImplementedError("%s.json(): not implemented yet." % self.__class__.__name__)

    def multipart(self):
        raise NotImplementedError("%s.multipart(): not implemented yet." % self.__class__.__name__)


class Response(object):

    def __init__(self):
        self.status   = 200
        self._headers = [('Content-Type', None), ('Content-Length', None)]
        self._cookies = []

    def add_header(self, name, val):
        self._headers.append((name, val))

    def add_cookie(self, name, val, domain=None, path=None, expires=None, maxage=None, httponly=None, secure=None):
        raise NotImplementedError("%s.add_cookie(): not implemented yet." % self.__class__.__name__)

    @property
    def content_type(self):
        self._headers[0][1]

    @content_type.setter
    def content_type(self, val):
        self._headers[0] = ('Content-Type', val)

    @property
    def content_length(self):
        s = self._headers[1][1]
        return None if s is None else int(s)

    @content_length.setter
    def content_length(self, val):
        self._headers[1] = ('Content-Length', str(val))

    def get_header_list(self):
        """don't access headers after get_header_list() called."""
        headers = self._headers
        self._headers = None
        if headers[1][1] is None:
            headers.pop(1)
        if headers[0][1] is None:
            headers.pop(0)
        return headers


class Application(object):

    def __init__(self, mapping):
        if isinstance(mapping, Router):
            self._router = mapping
        else:
            self._router = NaiveLinearRouter(mapping)

    def __call__(self, env, start_response):
        status, headers, body = self.handle_request(Request(env), Response())
        if isinstance(status, str):
            status_line = status
        else:
            status_line = HTTP_RESPONSE_STATUS_DICT.get(status) or "%s ???" % status
        start_response(status_line, headers)
        return body

    def handle_request(self, req, resp):
        meth = req.method; path = req.path
        handler_class, handler_func, param_args = \
            self._router.lookup(meth, path)
        if handler_class is None:
            #
            location = self.find_redirect_location(meth, path)
            if location:
                if req.query_string:
                    location += "?"+req.query_string
                resp.add_header("Location", location)
                body = self.content2body("redirect to " + location, resp)
                return 301, resp.get_header_list(), body
            #
            return self.http_error(404, req, resp)
        if handler_func is None:
            return self.http_error(405, req, resp)
        #
        handler_obj = handler_class(req, resp)
        content = handler_obj.handle_request(handler_func, param_args)
        body    = self.content2body(content, resp)
        if meth == 'HEAD':
            body = [b""]
        return resp.status, resp.get_header_list(), body

    def find_redirect_location(self, meth, path):
        if not (meth == 'GET' or meth == 'HEAD'):
            return None
        location = path[:-1] if path.endswith('/') else path+'/'
        if self._router.find(location) is None:
            return None
        return location

    def http_error(self, status_code, req, resp):
        status_line = HTTP_RESPONSE_STATUS_DICT.get(status_code)
        assert status_line is not None, "status_code=%r" % (status_code,)
        body = self.content2body("<h2>%s</h2>" % status_line, resp)
        return status_code, resp.get_header_list(), body

    def content2body(self, content, resp):
        if content is None:
            return [b""]
        if isinstance(content, dict):
            resp.content_type = "application/json"
            binary = self.dump_json(content).encode('utf-8')
            resp.content_length = len(binary)
            return [binary]
        if isinstance(content, str):
            if resp.content_type is None and content:
                c = content[0]
                resp.content_type = ("text/html;charset=utf-8" if c == '<' else
                                     "application/json"        if c == '{' else
                                     "text/plain;charset=utf-8")
            binary = content.encode('utf-8')
            resp.content_length = len(binary)
            return [binary]
        if isinstance(content, bytes):
            if not resp.content_type:
                resp.content_type = "application/octet-stream"
            resp.content_length = len(binary)
            binary = content
            return [binary]
        if hasattr(content, '__iter__'):
            if not resp.content_type:
                resp.content_type = "application/octet-stream"
            return content
        raise TypeError("unexpected content type: %s" % type(content))

    def dump_json(self, jdata, _separators=(',', ':')):
        return json.dumps(jdata, ensure_ascii=False, separators=_separators)


HTTP_RESPONSE_STATUS_DICT = {  # ref: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
  100: "100 Continue",
  101: "101 Switching Protocols",
  102: "102 Processing",                       # (WebDAV; RFC 2518)
  103: "103 Early Hints",                      # (RFC 8297)
  200: "200 OK",
  201: "201 Created",
  202: "202 Accepted",
  203: "203 Non-Authoritative Information",    # (since HTTP/1.1)
  204: "204 No Content",
  205: "205 Reset Content",
  206: "206 Partial Content",                  # (RFC 7233)
  207: "207 Multi-Status",                     # (WebDAV; RFC 4918)
  208: "208 Already Reported",                 # (WebDAV; RFC 5842)
  226: "226 IM Used",                          # (RFC 3229)
  300: "300 Multiple Choices",
  301: "301 Moved Permanently",
  302: "302 Found",                            # (Previously "Moved temporarily")
  303: "303 See Other",                        # (since HTTP/1.1)
  304: "304 Not Modified",                     # (RFC 7232)
  305: "305 Use Proxy",                        # (since HTTP/1.1)
  306: "306 Switch Proxy",
  307: "307 Temporary Redirect",               # (since HTTP/1.1)
  308: "308 Permanent Redirect",               # (RFC 7538)
  400: "400 Bad Request",
  401: "401 Unauthorized",                     # (RFC 7235)
  402: "402 Payment Required",
  403: "403 Forbidden",
  404: "404 Not Found",
  405: "405 Method Not Allowed",
  406: "406 Not Acceptable",
  407: "407 Proxy Authentication Required",    # (RFC 7235)
  408: "408 Request Timeout",
  409: "409 Conflict",
  410: "410 Gone",
  411: "411 Length Required",
  412: "412 Precondition Failed",              # (RFC 7232)
  413: "413 Payload Too Large",                # (RFC 7231)
  414: "414 URI Too Long",                     # (RFC 7231)
  415: "415 Unsupported Media Type",
  416: "416 Range Not Satisfiable",            # (RFC 7233)
  417: "417 Expectation Failed",
  418: "418 I'm a teapot",                     # (RFC 2324, RFC 7168)
  421: "421 Misdirected Request",              # (RFC 7540)
  422: "422 Unprocessable Entity",             # (WebDAV; RFC 4918)
  423: "423 Locked",                           # (WebDAV; RFC 4918)
  424: "424 Failed Dependency",                # (WebDAV; RFC 4918)
  426: "426 Upgrade Required",
  428: "428 Precondition Required",            # (RFC 6585)
  429: "429 Too Many Requests",                # (RFC 6585)
  431: "431 Request Header Fields Too Large",  # (RFC 6585)
  451: "451 Unavailable For Legal Reasons",    # (RFC 7725)
  500: "500 Internal Server Error",
  501: "501 Not Implemented",
  502: "502 Bad Gateway",
  503: "503 Service Unavailable",
  504: "504 Gateway Timeout",
  505: "505 HTTP Version Not Supported",
  506: "506 Variant Also Negotiates",          # (RFC 2295)
  507: "507 Insufficient Storage",             # (WebDAV; RFC 4918)
  508: "508 Loop Detected",                    # (WebDAV; RFC 5842)
  510: "510 Not Extended",                     # (RFC 2774)
  511: "511 Network Authentication Required",  # (RFC 6585)

  ## Unofficial codes
  #103: "103 Checkpoint",
  #218: "218 This is fine",                     # (Apache Web Server)
  #419: "419 Page Expired",                     # (Laravel Framework)
  #420: "420 Method Failure",                   # (Spring Framework)
  #420: "420 Enhance Your Calm",                # (Twitter)
  #450: "450 Blocked by Windows Parental Controls", # (Microsoft)
  #498: "498 Invalid Token",                    # (Esri)
  #499: "499 Token Required",                   # (Esri)
  #509: "509 Bandwidth Limit Exceeded",         # (Apache Web Server/cPanel)
  #526: "526 Invalid SSL Certificate",
  #530: "530 Site is frozen",
  #598: "598 (Informal convention) Network read timeout error",

  ## MS IIS
  #440: "440 Login Time-out",
  #449: "449 Retry With",
  #451: "451 Redirect",

  ## nginx
  #444: "444 No Response",
  #494: "494 Request header too large",
  #495: "495 SSL Certificate Error",
  #496: "496 SSL Certificate Required",
  #497: "497 HTTP Request Sent to HTTPS Port",
  #499: "499 Client Closed Request",

  ## Cloudflare
  #520: "520 Unknown Error",
  #521: "521 Web Server Is Down",
  #522: "522 Connection Timed Out",
  #523: "523 Origin Is Unreachable",
  #524: "524 A Timeout Occurred",
  #525: "525 SSL Handshake Failed",
  #526: "526 Invalid SSL Certificate",
  #527: "527 Railgun Error",
  #530: "530 Origin DNS Error",
}

### for debug

def new_env(meth, path, headers={}):
    pair = path.split('?', 1)
    if len(pair) == 2:
        path, qs = pair
    else:
        qs = ""
    env = {
        'REQUEST_METHOD' : meth,
        'PATH_INFO'      : path,
        'QUERY_STRING'   : qs,
    }
    for k, v in headers.items():
        name = 'HTTP_' + k.upper().replace('-', '_')
        env[name] = v
    setup_testing_defaults(env)
    return env


class StartResponse(object):

    def __init__(self):
        self.status  = None
        self.headers = None

    def __call__(self, status, headers):
        self.status  = status
        self.headers = headers

    def __repr__(self):
        klass = self.__class__.__name__
        return "%s(status=%r, headers=%r)" % (klass, self.status, self.headers)
