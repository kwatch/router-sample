# -*- coding: utf-8 -*-
# frozen_string_literal: true

##
## example router classes
##


$_has_moreregexp = false
if $opt_moreregexp    # enabled by '--moreregexp' option
  require_relative 'ext/moreregexp'
  $_has_moreregexp = true
end
if $opt_fastregexp
  require 'fast_regexp'
  REGEXP = Fast::Regexp
  class <<Fast::Regexp
    alias compile new
  end
else
  REGEXP = Regexp
end


require 'set' unless defined?(Set)


module K8


  REQUEST_METHODS = Set.new([
    :GET, :POST, :PUT, :DELETE, :PATCH, :HEAD, :OPTIONS, :TRACE, :CONNECT, # :ANY,
  ])


  class RequestHandler

    def self.mapping(path_pat, **methods)
      methods.each do |meth, symbol|
        REQUEST_METHODS.include?(meth) || meth == :ANY  or
          raise "#{meth.inspect}: unknown request method."
      end
      @__mapping__ ||= {}
      ! @__mapping__.key?(path_pat)  or
        raise "#{path_pat.inspect}: duplicated url path."
      @__mapping__[path_pat] = methods
    end

    def self.__mapping__
      return @__mapping__ ||= {}
    end

    def initialize(req, resp)
      @req  = req
      @resp = resp
    end

    attr_reader :req, :resp

    def before_request(handler, pvals)
    end

    def after_request(handler, pvals, exc)
    end

    def handle_request(handler, pvals)
      before_request(handler, pvals)   # ex: handler == :do_show, pvals == [123]
      exc = nil
      begin
        return invoke_handler(handler, pvals)
      rescue => exc
        raise
      ensure
        after_request(handler, pvals, exc)
      end
    end

    def invoke_handler(handler, pvals)
      return __send__(handler, *pvals)
    end

  end


  class Router

    def find(req_path)
      raise NotImplementedError.new("#{self.class.name}#find(): not implemented yet.")
    end

    protected

    def traverse(mapping, parent_path="", &b)
      mapping.each do |path, child|
        case child
        when Hash
          traverse(child, parent_path + path, &b)
        when Class
          klass = child
          klass < RequestHandler  or
            raise "#{klass.inspect}: not a subclass of RequestHandler."
          yield parent_path + path, klass
        else
          raise "#{child.inspect}: expected handler class or child mapping."
        end
      end
    end

    def each_handler(mapping, parent_path="", &b)
      traverse(mapping, parent_path) do |path_pat, handler_class|
        handler_class.__mapping__.each do |subpath, handler_methods|
          yield "#{path_pat}#{subpath}", handler_class, handler_methods
        end
      end
    end

    def fixed_path?(path_pat)
      return true if path_pat !~ /\{/
      return true if path_pat.end_with?('.*')
      return false
    end

    def path2rexpstr(urlpath_pat, left='(?:', right=')', beg=nil, end_=nil)
      pnames = []
      ptypes = []
      buf = []
      buf << beg if beg
      scan_params(urlpath_pat) do |text, pname, ptype, prexp|
        buf << Regexp.escape(text) if ! text.empty?
        buf << left << prexp << right if prexp
        pnames << pname if pname
        ptypes << ptype if ptype
      end
      buf << end_ if end_
      return buf.join(), pnames, ptypes
    end

    def scan_params(urlpath_pat)
      ptype_rexp_strs = PARAM_TYPE_PATTERNS
      pos = 0
      urlpath_pat.scan(/\{(.*?)\}/) do
        m = Regexp.last_match
        text  = urlpath_pat[pos...m.begin(0)]
        pos   = m.end(0)
        param = m[1]
        param =~ /\A(\w+)(?::(\w*))?\z/  or
          raise "#{urlpath_pat}: invalid parameter '{#{param}}'."
        pname = $1
        ptype = $2 || guess_param_type(pname)
        prexp = ptype_rexp_strs[ptype]  or
          raise "#{urlpath_pat}: invalid parameter type '#{ptype}'."
        yield text, pname, ptype.intern, prexp
      end
      rest = (pos == 0 ? urlpath_pat : urlpath_pat[pos..-1])
      yield rest, nil, nil, nil if ! rest.empty?
    end

    def parse_param(param)
      param =~ /\A(\w+)(?::(\w+))?\z/  or
        raise "'{#{param}}': invalid parameter ."
      pname = $1
      ptype = $2
      if ptype
        PARAM_TYPE_PATTERNS[ptype]  or
          raise "'{#{param}}'unknown parameter type."
      else
        ptype = guess_param_type(pname)
      end
      return pname, ptype.intern
    end

    def guess_param_type(pname)
      return 'int' if pname == 'id'
      return 'int' if pname =~ /_id\z/
      return 'str'
    end

    PARAM_TYPE_PATTERNS = {
      #'int'  => '\d+',
      'int'  => '[1-9]\d*',
      'str'  => '[^\/.]+',
      'path' => '.*',
    }

    def valid_suffix?(actual_suffix, expected_suffix)
      return true if actual_suffix == expected_suffix
      return true if expected_suffix == '.*'
      return false
    end

  end


  class NaiveLinearRouter < Router

    def initialize(mapping)
      @entries = []
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
        urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
        @entries << [urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
      end
    end

    def find(req_path)
      @entries.each do |tuple|
        urlpath_rexp, handler_class, handler_methods, pnames, ptypes = tuple
        m = urlpath_rexp.match(req_path)
        if m
          pvals = []
          strs = m.captures()
          i = -1; n = strs.length
          while (i += 1) < n
            pvals << (ptypes[i] == :int ? strs[i].to_i : strs[i])
          end
          return handler_class, handler_methods, pvals
        end
      end
      return nil
    end

  end


  class PrefixLinearRouter < Router

    def initialize(mapping)
      @entries = []
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
        urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
        prefix = urlpath_pat.split(/\{/, 2)[0]
        @entries << [prefix, urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
      end
    end

    def find(req_path)
      @entries.each do |tuple|
        prefix = tuple[0]
        next if ! req_path.start_with?(prefix)
        _, urlpath_rexp, handler_class, handler_methods, pnames, ptypes = tuple
        m = urlpath_rexp.match(req_path)
        if m
          strs = m.captures()
          pvals = []
          i = -1; n = strs.length
          while (i += 1) < n
            pvals << (ptypes[i] == :int ? strs[i].to_i : strs[i])
          end
          return handler_class, handler_methods, pvals
        end
      end
      return nil
    end

  end


  class FixedLinearRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      @entries = []
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
          urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
          prefix = urlpath_pat.split(/\{/, 2)[0]
          @entries << [prefix, urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
        end
      end
    end

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      @entries.each do |tuple|
        prefix = tuple[0]
        next if ! req_path.start_with?(prefix)
        _, urlpath_rexp, handler_class, handler_methods, pnames, ptypes = tuple
        m = urlpath_rexp.match(req_path)
        if m
          strs = m.captures()
          pvals = []
          i = -1; n = strs.length
          while (i += 1) < n
            pvals << (ptypes[i] == :int ? strs[i].to_i : strs[i])
          end
          return handler_class, handler_methods, pvals
        end
      end
      return nil
    end

  end


  class HashedLinearRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      entries = []
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
          urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
          prefix = urlpath_pat.split(/\{/, 2)[0]
          entries << [prefix, urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
        end
      end
      #
      minlen = nil
      entries.each do |tuple|
        prefix = tuple[0]
        len = prefix.length
        minlen = len if ! minlen || len < minlen
      end
      @key_length = minlen
      #
      @entries_dict = {}
      entries.each do |tuple|
        prefix = tuple[0]
        key = prefix[0, minlen]
        key = nil if key =~ /\{/
        (@entries_dict[key] ||= []) << tuple
      end
      @entries_dict[nil] ||= []
    end

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      key = req_path[0, @key_length]
      entries = @entries_dict[key] || @entries_dict[nil]
      entries.each do |tuple|
        prefix = tuple[0]
        next if ! req_path.start_with?(prefix)
        _, urlpath_rexp, handler_class, handler_methods, pnames, ptypes = tuple
        m = urlpath_rexp.match(req_path)
        if m
          strs = m.captures()
          pvals = []
          i = -1; n = strs.length
          while (i += 1) < n
            pvals << (ptypes[i] == :int ? strs[i].to_i : strs[i])
          end
          return handler_class, handler_methods, pvals
        end
      end
      return nil
    end

  end


  class NaiveRegexpRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      @entries = []
      buf = ['\A(?:']
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
          urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
          @entries << [urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
          index = @entries.length - 1
          buf << "(?<_#{index}>" << rexp_str << ")" << "|"
        end
      end
      buf.pop() if buf[-1] == "|"
      buf << ')\z'
      @regexp = REGEXP.compile(buf.join())
    end

    attr_reader :regexp

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      m = @regexp.match(req_path)
      return nil unless m
      d = m.named_captures        # ex: {"_1"=>nil, "_2"=>nil, "_3"=>"/api/books/123"}
      key = d.compact.keys.first  # ex: "_3"
      index = key[1..-1].to_i     # ex: 3
      #
      t = @entries[index]  or
        raise "** internal error: index=#{index.inspect}"
      urlpath_rexp, handler_class, handler_methods, pnames, ptypes = t
      m2 = urlpath_rexp.match(req_path)  or
        raise "** internal error: urlpath_rexp=#{urlpath_rexp.inspect}"
      strs = m2.captures()
      pvals = []
      i = -1; n = strs.length
      while (i += 1) < n
        pval = strs[i]
        pvals << (ptypes[i] == :int ? pval.to_i : pval)
      end
      return handler_class, handler_methods, pvals
    end

  end


  class SmartRegexpRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      @entries = []
      empty_pvals = [].freeze
      @regexp = compile(mapping) do
        |urlpath_pat, urlpath_rexp, handler_class, handler_methods, pnames, ptypes|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          @entries << [urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
        end
      end
    end

    attr_reader :regexp

    protected

    def compile(mapping)
      buf = ['^(?:']
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if urlpath_pat !~ /\{/
          urlpath_rexp = pnames = ptypes = nil
        else
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(?:', ')')
          buf << rexp_str << '($)' << '|'
          urlpath_rexp = REGEXP.compile('\A' + rexp_str.gsub('(?:', '(') + '\z')
        end
        yield urlpath_pat, urlpath_rexp, handler_class, handler_methods, pnames, ptypes
      end
      buf.pop() if buf[-1] == '|'
      buf << ')'
      return REGEXP.compile(buf.join())
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      m1 = @regexp.match(req_path)
      return nil unless m1
      if $_has_moreregexp
        index = m1.first_capture_number() - 1
      else
        index = m1.captures.index("")
      end
      #
      t = @entries[index]
      urlpath_rexp, handler_class, handler_methods, pnames, ptypes = t
      m2 = urlpath_rexp.match(req_path)  or
        raise "** internal error: #{urlpath_rexp.inspect}.match(#{req_path.inspect}) should not be nil."
      #pvals = []
      #m2.captures().zip(ptypes) do |pval, ptype|
      #  pvals << (ptype == :int ? pval.to_i : pval)
      #end
      strs = m2.captures()
      pvals = []
      i = -1; n = strs.length
      while (i += 1) < n
        pval = strs[i]
        pvals << (ptypes[i] == :int ? pval.to_i : pval)
      end
      return handler_class, handler_methods, pvals
    end

  end


  class NestedRegexpRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      @entries = []
      empty_pvals = [].freeze
      rexp_str = traverse2(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
          index = nil
        else
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
          urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
          @entries << [urlpath_rexp, handler_class, handler_methods, pnames, ptypes]
          index = @entries.length - 1
        end
        index
      end
      @regexp = REGEXP.compile('\A' + rexp_str + '\z')
    end

    attr_reader :regexp

    protected

    def traverse2(mapping, parent_path="", &b)
      buf1 = []
      mapping.each do |path_pat, child|
        base_path = "#{parent_path}#{path_pat}"
        case child
        when Hash
          child_rexp_str = traverse2(child, base_path, &b)
        when Class
          handler_class = child
          buf2 = []
          handler_class.__mapping__.each do |subpath, handler_methods|
            index = yield "#{base_path}#{subpath}", handler_class, handler_methods
            if index
              rexp_str2, _, _ = path2rexpstr(subpath, '(?:', ')')
              buf2 << "#{rexp_str2}($)"
            end
          end
          child_rexp_str = join_rexp_strs(buf2)
        else
          raise "#{child.inspect}: expected handler class or child mapping."
        end
        rexp_str1, _, _ = path2rexpstr(path_pat, '(?:', ')')
        buf1 << "#{rexp_str1}#{child_rexp_str}" if child_rexp_str
      end
      return join_rexp_strs(buf1)
    end

    def join_rexp_strs(buf)
      return nil if buf.empty?
      return buf[0] if buf.length == 1
      return "(?:#{buf.join('|')})"
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      m1 = @regexp.match(req_path)
      return nil unless m1
      if $_has_moreregexp
        index = m1.first_capture_number() - 1
      else
        index = m1.captures.index("")
      end
      #
      t = @entries[index]
      urlpath_rexp, handler_class, handler_methods, _pnames, ptypes = t
      m2 = urlpath_rexp.match(req_path)  or
        raise "** internal error: #{urlpath_rexp.inspect}.match(#{req_path.inspect}) should not be nil."
      #pvals = []
      #m2.captures().zip(ptypes) do |pval, ptype|
      #  pvals << (ptype == :int ? pval.to_i : pval)
      #end
      strs = m2.captures()
      pvals = []
      i = -1; n = strs.length
      while (i += 1) < n
        pval = strs[i]
        pvals << (ptypes[i] == :int ? pval.to_i : pval)
      end
      return handler_class, handler_methods, pvals
    end

  end


  class OptimizedRegexpRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      entries1 = []
      empty_pvals = [].freeze
      root_node = []
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          elems = []
          scan_params(urlpath_pat) do |text, pname, ptype, prexp|
            elems << text
            elems << ptype if ptype
          end
          rexp_str, pnames, ptypes = path2rexpstr(urlpath_pat, '(', ')')
          urlpath_rexp = REGEXP.compile('\A' + rexp_str + '\z')
          entries1 << [urlpath_rexp, handler_class, handler_methods, pnames, ptypes, urlpath_pat]
          index = entries1.length - 1
          build_tree(root_node, elems, index)
        end
      end
      @entries = reorder_entries(entries1, root_node)
      entries1.compact.empty?  or
        raise "** internal error: entries1=#{entries1.inspect}"
      rexp_str2 = compile_tree(root_node)
      @regexp = REGEXP.compile('\A' + rexp_str2 + '\z')
    end

    attr_reader :regexp

    protected

    def build_tree(node, elems, index, &b)
      elems.each do |elem|
        found = false
        case elem
        when Symbol
          ptype = elem
          node.each do |(path, child)|
            next if ! path
            if path == ptype
              node = child
              found = true
              break
            end
          end
        when String
          urlpath_pat = elem
          i = -1
          while (i += 1) < node.length
            path, child = node[i]
            next if ! path
            prefix = shared_prefix(path, urlpath_pat)
            if prefix && ! prefix.empty?
              subpath1 = path[prefix.length..-1]
              subpath2 = urlpath_pat[prefix.length..-1]
              if subpath1.empty? && subpath2.empty?
                node = child
                found = true
                break
              elsif subpath1.empty?
                i = -1
                node = child
                elem = urlpath_pat = subpath2
                next
              else
                node2 = []
                node[i] = [prefix, [
                             [subpath1, child],
                             [subpath2, node2],
                           ]]
                node = node2
                found = true
                break
              end
            end
          end
        else
          raise "** internal error: elem=#{elem.inspect}"
        end
        if ! found
          node2 = []
          node << [elem, node2]
          node = node2
        end
      end
      node << [nil, index]
    end

    def reorder_entries(entries1, node, entries2=[])
      node.each do |path, child|
        case child
        when Array
          reorder_entries(entries1, child, entries2)
        when Integer
          index = child
          entries1[index] != nil  or
            raise "** internal error: index=#{index.inspect}"
          entries2 << entries1[index]
          entries1[index] = nil
        else
          raise "** internal error: child=#{child.inspect}"
        end
      end
      return entries2
    end

    def compile_tree(node)
      buf = []
      i = 0
      node.each do |path, child|
        i += 1
        buf << "|" if i > 1
        case path
        when nil
          buf << "($)"
          child.is_a?(Integer)  or
            raise "** internal error: child=#{child.inspect}"
        when String
          buf << Regexp.escape(path)
          buf << compile_tree(child)
        when Symbol
          ptype = path
          rexp_str = PARAM_TYPE_PATTERNS[ptype.to_s]  or
            raise "** internal error: ptype=#{ptype.inspect}"
          buf << rexp_str
          buf << compile_tree(child)
        end
      end
      if i > 1
        buf.unshift("(?:")
        buf << ")?"
      end
      return buf.join()
    end

    def shared_prefix(s1, s2)
      return nil if s1[0] != s2[0]
      n1 = s1.length; n2 = s2.length
      n = n1 < n2 ? n1 : n2
      i = 0
      while (i += 1) < n && s1[i] == s2[i]
        nil
      end
      return s1[0...i]
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      m1 = @regexp.match(req_path)
      return nil unless m1
      if $_has_moreregexp
        index = m1.first_capture_number() - 1
      else
        index = m1.captures.index("")
      end
      #
      t = @entries[index]
      urlpath_rexp, handler_class, handler_methods, _pnames, ptypes, _urlpath_pat = t
      m2 = urlpath_rexp.match(req_path)  or
        raise "** internal error: #{urlpath_rexp.inspect}.match(#{req_path.inspect}) should not be nil."
      #pvals = []
      #m2.captures().zip(ptypes) do |pval, ptype|
      #  pvals << (ptype == :int ? pval.to_i : pval)
      #end
      strs = m2.captures()
      pvals = []
      i = -1; n = strs.length
      while (i += 1) < n
        pval = strs[i]
        pvals << (ptypes[i] == :int ? pval.to_i : pval)
      end
      return handler_class, handler_methods, pvals
    end

  end


  class SlicedRegexpRouter < OptimizedRegexpRouter

    def initialize(mapping)
      super
      @entries.each do |t|
        urlpath_pat = t[-1]
        arr = urlpath_pat.split(/\{.*?\}/, -1)
        if arr.length == 2
          range = arr[0].length..-(arr[1].length+1)
          t << range << nil
        elsif arr.length == 3
          range = arr[0].length..-(arr[2].length+1)
          t << range << arr[1]
        end
      end
    end

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      m1 = @regexp.match(req_path)
      return nil unless m1
      if $_has_moreregexp
        index = m1.first_capture_number() - 1
      else
        index = m1.captures.index("")
      end
      #
      t = @entries[index]
      urlpath_rexp, handler_class, handler_methods, _pnames, ptypes, _urlpath_pat, range, separator = t
      if range
        str = req_path[range]
        strs = separator ? str.split(separator, -1) : [str]
      else
        m2 = urlpath_rexp.match(req_path)  or
          raise "** internal error: #{urlpath_rexp.inspect}.match(#{req_path.inspect}) should not be nil."
        strs = m2.captures()
      end
      pvals = []
      i = -1; n = strs.length
      while (i += 1) < n
        pval = strs[i]
        pvals << (ptypes[i] == :int ? pval.to_i : pval)
      end
      return handler_class, handler_methods, pvals
    end

  end


  class HashedRegexpRouter < Router
    SUBROUTER_CLASS = OptimizedRegexpRouter

    def initialize(mapping)
      @fixed_paths   = {}
      @subrouters    = {}
      @prefix_length = nil
      #
      pairs = []
      minlen = nil
      traverse(mapping, "") do |path_pat, handler_class|
        pairs << [path_pat, handler_class]
        idx = path_pat.index('{') || path_pat.length
        minlen = idx if minlen == nil || idx < minlen
      end
      @prefix_length = minlen || 0
      #
      prefixed_pairs = {}
      pairs.each do |pair|
        path_pat = pair[0]
        prefix = path_pat[0, minlen]
        if prefix =~ /\{/
          prefix = nil
        end
        (prefixed_pairs[prefix] ||= []) << pair
      end
      #
      subrouter_class = self.class.const_get(:SUBROUTER_CLASS)
      prefixed_pairs.each do |prefix, pairs|
        submapping = pairs
        subrouter = subrouter_class.new(submapping)
        @subrouters[prefix] = subrouter
        dict = subrouter.instance_variable_get(:@fixed_paths)
        @fixed_paths.update(dict)
        dict.clear()
      end
    end

    def dispatch_subrouter(req_path)
      prefix = req_path[0, @prefix_length]
      subrouter = @subrouters[prefix] || @subrouters[nil]
      return subrouter
    end

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      prefix = req_path[0, @prefix_length]
      subrouter = @subrouters[prefix] || @subrouters[nil]
      return nil if subrouter == nil
      return subrouter.find(req_path)
    end

  end

  class HashedRegexpRouter1 < HashedRegexpRouter
    SUBROUTER_CLASS = OptimizedRegexpRouter
  end

  class HashedRegexpRouter2 < HashedRegexpRouter
    SUBROUTER_CLASS = SlicedRegexpRouter
  end


  class ListBasedTrieRouter < Router

    class Node
      def initialize(key)
        @key      = key
        @children = []
        @target   = nil
      end
      attr_reader :key
      #attr_reader :children
      attr_accessor :target
      def find(key)
        return @children.find {|child| child.key == key}
      end
      def insert(key)
        node = find(key)
        if ! node
          node = Node.new(key)
          @children << node
        end
        return node
      end
    end

    def initialize(mapping)
      @fixed_paths = {}
      @entries     = []
      @root_node   = Node.new(nil)
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          register(@root_node, urlpath_pat) do |node, suffix|
            node.target == nil  or
              raise "#{urlpath_pat}: duplicated path registered."
            node.target = [handler_class, handler_methods, suffix]
          end
        end
      end
    end

    protected

    def register(node, urlpath_pat, &b)
      suffix = File.extname(urlpath_pat)
      if suffix.empty?
        suffix = nil
        path_pat = urlpath_pat
      else
        path_pat = urlpath_pat[0...-suffix.length]
      end
      items = path_pat.split('/')
      items.shift() if path_pat.start_with?('/')
      items.each do |item|
        if item =~ /\A\{(.*?)\}\z/
          _pname, ptype = parse_param($1)
          key = ptype
        else
          key = item
        end
        node = node.insert(key)
      end
      yield node, suffix
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      suffix = File.extname(req_path)
      if suffix.empty?
        suffix = nil
        rpath = req_path
      else
        rpath = req_path[0...-suffix.length]
      end
      #
      items = rpath.split('/')
      i = rpath.start_with?('/') ? 0 : -1
      n = items.length
      node = @root_node
      pvalues = []
      while (i += 1) < n
        item = items[i]
        if (node2 = node.find(item))
          nil
        #elsif (node2 = node.find(:int)) && item =~ /\A\d+\z/
        #elsif (node2 = node.find(:int)) && item =~ /\A[1-9]\d*\z/
        #elsif (node2 = node.find(:int)) && item.digits?
        #elsif (node2 = node.find(:int)) && item.digits_starting_nonzero?
        #  pvalues << item.to_i
        elsif (node2 = node.find(:int)) && (x = item.to_i) > 0 && x.to_s == item
          pvalues << x
        elsif (node2 = node.find(:str))
          pvalues << item
        else
          return nil
        end
        node = node2
      end
      #
      return nil if node.target == nil
      handler_class, handler_methods, expected_suffix = node.target
      return nil unless valid_suffix?(suffix, expected_suffix)
      return handler_class, handler_methods, pvalues
    end

  end


  class DictBasedTrieRouter < Router

    class Node
      def initialize()
        @children = {}
        @target   = nil
      end
      #attr_reader :children
      attr_accessor :target
      def find(key)
        return @children[key]
      end
      def insert(key)
        node = find(key)
        if ! node
          node = Node.new
          @children[key] = node
        end
        return node
      end
    end

    def initialize(mapping)
      @fixed_paths = {}
      @entries     = []
      @root_node   = Node.new
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          register(@root_node, urlpath_pat) do |node, suffix|
            node.target == nil  or
              raise "#{urlpath_pat}: duplicated path registered."
            node.target = [handler_class, handler_methods, suffix]
          end
        end
      end
    end

    protected

    def register(node, urlpath_pat, &b)
      suffix = File.extname(urlpath_pat)
      if suffix.empty?
        suffix = nil
        path_pat = urlpath_pat
      else
        path_pat = urlpath_pat[0...-suffix.length]
      end
      items = path_pat.split('/')
      items.shift() if path_pat.start_with?('/')
      items.each do |item|
        if item =~ /\A\{(.*?)\}\z/
          _pname, ptype = parse_param($1)
          key = ptype
        else
          key = item
        end
        node = node.insert(key)
      end
      yield node, suffix
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      suffix = File.extname(req_path)
      if suffix.empty?
        suffix = nil
        rpath = req_path
      else
        rpath = req_path[0...-suffix.length]
      end
      #
      items = rpath.split('/')
      i = rpath.start_with?('/') ? 0 : -1
      n = items.length
      node = @root_node
      pvalues = []
      while (i += 1) < n
        item = items[i]
        if (node2 = node.find(item))
          nil
        #elsif (node2 = node.find(:int)) && item =~ /\A\d+\z/
        #elsif (node2 = node.find(:int)) && item =~ /\A[1-9]\d*\z/
        #elsif (node2 = node.find(:int)) && item.digits?
        #elsif (node2 = node.find(:int)) && item.digits_starting_nonzero?
        #  pvalues << item.to_i
        elsif (node2 = node.find(:int)) && (x = item.to_i) > 0 && x.to_s == item
          pvalues << x
        elsif (node2 = node.find(:str))
          pvalues << item
        else
          return nil
        end
        node = node2
      end
      #
      return nil if node.target == nil
      handler_class, handler_methods, expected_suffix = node.target
      return nil unless valid_suffix?(suffix, expected_suffix)
      return handler_class, handler_methods, pvalues
    end

  end


  class StateMachineRouter < Router

    def initialize(mapping)
      @fixed_paths      = {}    # ex: {"/books/"=>[BooksHandler, {:GET=>:do_show}, []]}
      @entries          = []    # ex: [[BooksHandler, {:GET=>:do_show}, ".json"], ...]
      @transition_maps  = [{}]  # ex: [{"books"=>1,"users"=>2},{:int=>2},{nil=>[...]}]
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          register(urlpath_pat, @transition_maps) do |last_map, suffix|
            d = last_map
            d[nil] == nil  or
              raise "#{urlpath_pat}: duplicated path registered."
            @entries << [handler_class, handler_methods, suffix]
            d[nil] = @entries.length - 1
          end
        end
      end
    end

    protected

    def register(urlpath_pat, transition_maps, &b)
      suffix = File.extname(urlpath_pat)
      if suffix.empty?
        suffix = nil
        path_pat = urlpath_pat
      else
        path_pat = urlpath_pat[0...-suffix.length]
      end
      #pnames = []
      #ptypes = []
      items = path_pat.split('/')
      items.shift() if path_pat.start_with?('/')
      d = transition_maps[0]
      items.each do |item|
        if item =~ /\A\{(.*?)\}\z/
          _pname, ptype = parse_param($1)
          #pnames << _pname
          #ptypes << ptype
          key = ptype
        else
          key = item
        end
        if d[key]
          index = d[key]
        else
          transition_maps << {}
          index = transition_maps.length - 1
          d[key] = index
        end
        d = transition_maps[index]
      end
      last_dict = d
      yield last_dict, suffix
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      suffix = File.extname(req_path)
      if suffix.empty?
        suffix = nil
        rpath = req_path
      else
        rpath = req_path[0...-suffix.length]
      end
      #
      transition_maps = @transition_maps
      items = rpath.split('/')
      i = rpath.start_with?('/') ? 0 : -1
      n = items.length
      d = transition_maps[0]
      pvalues = []
      while (i += 1) < n
        item = items[i]
        if (index = d[item])
          nil
        #elsif (d2 = d[:int]) && item =~ /\A\d+\z/
        #elsif (d2 = d[:int]) && item =~ /\A[1-9]\d*\z/
        #elsif (d2 = d[:int]) && item.digits?
        #elsif (d2 = d[:int]) && item.digits_starting_nonzero?
        #  pvalues << item.to_i
        elsif (index = d[:int]) && (x = item.to_i) > 0 && x.to_s == item
          pvalues << x
        elsif (index = d[:str])
          pvalues << item
        else
          return nil
        end
        d = transition_maps[index]
      end
      #
      index = d[nil]
      return nil if ! index
      handler_class, handler_methods, expected_suffix = @entries[index]
      return nil unless valid_suffix?(suffix, expected_suffix)
      return handler_class, handler_methods, pvalues
    end

  end


  class NestedDictRouter < Router

    def initialize(mapping)
      @fixed_paths = {}
      @entries     = []
      @root_table  = {}
      empty_pvals = [].freeze
      each_handler(mapping) do |urlpath_pat, handler_class, handler_methods|
        if fixed_path?(urlpath_pat)
          @fixed_paths[urlpath_pat] = [handler_class, handler_methods, empty_pvals]
        else
          register(@root_table, urlpath_pat) do |leaf_node, suffix|
            d = leaf_node
            d[nil] == nil  or
              raise "#{urlpath_pat}: duplicated path registered."
            @entries << [handler_class, handler_methods, suffix]
            index = @entries.length - 1
            d[nil] = index
          end
        end
      end
    end

    protected

    def register(root_table, urlpath_pat, &b)
      suffix = File.extname(urlpath_pat)
      if suffix.empty?
        suffix = nil
        path_pat = urlpath_pat
      else
        path_pat = urlpath_pat[0...-suffix.length]
      end
      #pnames = []
      #ptypes = []
      items = path_pat.split('/')
      items.shift() if path_pat.start_with?('/')
      d = root_table
      items.each do |item|
        if item =~ /\A\{(.*?)\}\z/
          _pname, ptype = parse_param($1)
          #pnames << _pname
          #ptypes << ptype
          key = ptype
        else
          key = item
        end
        d = (d[key] ||= {})
      end
      leaf_node = d
      yield leaf_node, suffix
    end

    public

    def find(req_path)
      trio = @fixed_paths[req_path]
      return trio if trio
      #
      suffix = File.extname(req_path)
      if suffix.empty?
        suffix = nil
        rpath = req_path
      else
        rpath = req_path[0...-suffix.length]
      end
      #
      items = rpath.split('/')
      i = rpath.start_with?('/') ? 0 : -1
      n = items.length
      d = @root_table
      pvalues = []
      while (i += 1) < n
        item = items[i]
        if (d2 = d[item])
          nil
        #elsif (d2 = d[:int]) && item =~ /\A\d+\z/
        #elsif (d2 = d[:int]) && item =~ /\A[1-9]\d*\z/
        #elsif (d2 = d[:int]) && item.digits?
        #elsif (d2 = d[:int]) && item.digits_starting_nonzero?
        #  pvalues << item.to_i
        elsif (d2 = d[:int]) && (x = item.to_i) > 0 && x.to_s == item
          pvalues << x
        elsif (d2 = d[:str])
          pvalues << item
        else
          return nil
        end
        d = d2
      end
      #
      index = d[nil]
      return nil if ! index
      handler_class, handler_methods, expected_suffix = @entries[index]
      return nil unless valid_suffix?(suffix, expected_suffix)
      return handler_class, handler_methods, pvalues
    end

  end


  #---


  class Request

    METHOD_DICT = REQUEST_METHODS.each_with_object({}) {|sym, d| d[sym.to_s] = sym }

    def initialize(env)
      req_meth_str = env['REQUEST_METHOD']
      @meth = METHOD_DICT[req_meth_str]
      @path = env['PATH_INFO']
      @query_str = env['QUERY_STRING']
      @env = env
    end

    attr_reader :meth, :path, :env, :query_str

    def each_header(&b)
      return enum_for(:each_header) unless block_given?()
      env = @env
      env.each do |name, val|
        if name.start_with?('HTTP_')
          yield name[6..-1], val
        end
      end
      nil
    end

    def get_header(name)
      return @env["HTTP_#{name}"]
    end

  end


  class Response

    def initialize(status_code)
      @status_code    = status_code
      @content_type   = nil
      @content_length = nil
      @headers        = {}
    end

    attr_reader :status_code, :headers
    attr_accessor :content_type, :content_length

    def get_header(name)
      return @headers[name]
    end

    def set_header(name, value)
      @headers[name] = value
      value
    end

    def add_header(name, value)
      val = @headers[name]
      if val
        @headers[name] = "#{val}\n#{value}"
      else
        @headers[name] = value
      end
      value
    end

  end


  class Application

    def initialize(router)
      @router = router
    end

    attr_reader :router

    def call(env)
      handle_request(env)
    end

    protected

    def handle_request(env)
      req  = Request.new(env)
      resp = Response.new
      trio = @router.find(req.path)
      if ! trio
        if (x = req.meth) == :GET || x == :HEAD
          redirect_path = req.path.end_with?('/') ? req.path.chomp('/') : req.path + '/'
          trio = @router.find(redirect_path)
          return http_301(req, resp, redirect_path) if trio
        end
        return http_404(req, resp)
      end
      handler_klass, handler_methods, param_values = trio
      d = handler_methods
      handler_method = d[req.meth] || (req.meth == :HEAD ? d[:GET] : nil) || d[:ANY]  or
        return http_405(req, resp)
      handler_obj = handler_klass.new(req, resp)
      begin
        content = handler_obj.handle_request(hander_method, param_values)
        return handle_response(req, resp, content)
      rescue => exc
        return http_500(req, resp, exc)
      end
    end

    def handle_response(req, resp, content)
      tuple = content2body(content)  or
        raise HttpError(500, "#{content.class.name}: invalid response body class.")
      ctype, clen, body = tuple
      ctype = resp.content_type   || ctype
      clen  = resp.content_length || clen
      status_code = resp.status_code || 200
      headers = {"Content-Type" => ctype}
      headers["Content-Length"] ||= clen.to_s if clen
      headers.update(resp.headers)
      return [status_code, headers, body]
    end

    def content2body(content)
      case content
      when Hash
        ctype = "application/json"
        text = JSON.generate(content)
        clen = body.bytesize
        body = [text]
      when String
        ctype = "text/html;charset=utf-8"
        text = content
        clen = body.bytesize
        body = [text]
      when Array, Enumerable
        ctype = "text/html;charset=utf-8"
        text = nil
        clen = nil
        body = content
      when nil
        ctype = "text/plain;charset=utf-8"
        text = ""
        clen = 0
        body = [text]
      else
        return nil
      end
      return ctype, clen, body
    end

    def http_301(req, resp, redirect_path)
      qstr = req.env['QUERY_STRING']
      if qstr && ! qstr.empty?
        redirect_path += "?#{qstr}"
      end
      headers = {"Content-Type" => "text/plain;charset=utf-8",
                 "Location" => redirect_path}
      return [301, headers, "Redirect to #{redirect_path}"]
    end

    def http_404(req, resp)
      headers = {"Content-Type" => "text/plain;charset=utf-8"}
      return [404, headers, "404 Not Found"]
    end

    def http_405(req, resp)
      headers = {"Content-Type" => "text/plain;charset=utf-8"}
      return [405, headers, "405 Method Not Allowed"]
    end

    def http_500(req, resp, exc)
      headers = {"Content-Type" => "text/plain;charset=utf-8"}
      return [500, headers, "500 Internal Server Error"]
    end

  end


end
