# -*- coding: utf-8 -*-
# frozen_string_literal: true

require 'benchmarker'  # https://kwatch.github.io/benchmarker/ruby.html

require './minikeight'

router_classes = [
  K8::NaiveLinearRouter,
  K8::PrefixLinearRouter,
  K8::FixedLinearRouter,
  K8::HashedLinearRouter,
  #
  K8::NaiveRegexpRouter,
  K8::SmartRegexpRouter,
  K8::NestedRegexpRouter,
  K8::OptimizedRegexpRouter,
  K8::SlicedRegexpRouter,
  K8::HashedRegexpRouter,
 #K8::HashedRegexpRouter1,
 #K8::HashedRegexpRouter2,
  #
  K8::ListBasedTrieRouter,
  K8::DictBasedTrieRouter,
  K8::StateMachineRouter,
  K8::NestedDictRouter,
]


class HelloAPI < K8::RequestHandler
  mapping "/"         , :GET=>:do_list, :POST=>:do_create
  mapping "/new"      , :GET=>:do_new
  mapping "/{id}.json", :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping "/{id}/edit", :GET=>:do_edit
  def do_list()     ; return {type: "list"}           ; end
  def do_create()   ; return {type: "create"}         ; end
  def do_new()      ; return {type: "new"}            ; end
  def do_show(id)   ; return {type: "show"  , id: id} ; end
  def do_update(id) ; return {type: "update", id: id} ; end
  def do_delete(id) ; return {type: "delete", id: id} ; end
  def do_edit(id)   ; return {type: "edit"  , id: id} ; end
end

class CommentAPI < K8::RequestHandler
  mapping "/"         , :GET=>:do_list, :POST=>:do_create
  mapping "/new"      , :GET=>:do_new
  mapping "/{id}.json", :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping "/{id}/edit", :GET=>:do_edit
  def do_list(id)         ; return {type: "list"}           ; end
  def do_create(id)       ; return {type: "create"}         ; end
  def do_new(id)          ; return {type: "new"}            ; end
  def do_show(id, c_id)   ; return {type: "show"  , id: id} ; end
  def do_update(id, c_id) ; return {type: "update", id: id} ; end
  def do_delete(id, c_id) ; return {type: "delete", id: id} ; end
  def do_edit(id, c_id)   ; return {type: "edit"  , id: id} ; end
end

class DummyAPI < K8::RequestHandler
  mapping "", :GET=>:do_nothing
  def do_nothing(*args)
    return {args: args}
  end
end

benchdata = ENV['BENCHDATA']
case benchdata
when nil, "", "default"

  mapping = {
    "/api" => {
      "/aaa" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/bbb" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ccc" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ddd" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/eee" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/fff" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ggg" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/hhh" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/iii" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/jjj" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/kkk" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/lll" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/mmm" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/nnn" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ooo" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ppp" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/qqq" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/rrr" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/sss" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/ttt" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/uuu" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/vvv" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/www" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/xxx" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/yyy" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
      "/zzz" => {"" => HelloAPI, "/{id}/comments" => CommentAPI},
    }
  }

  request_paths = [
    #"/api/aaa/",
    "/api/aaa/123.json",
    "/api/aaa/123/comments/888.json",
    #"/api/zzz/",
    "/api/zzz/456.json",
    "/api/zzz/456/comments/999.json",
  ]

  width = 52

when "githubapi"

  dict = {}
  File.open("data/github-api-paths.txt") do |f|
    f.each do |line|
      line = line.strip
      next if line.empty?
      next if line =~ /^#/
      urlpath_pat = line.gsub(/\{(.*?)\}/) { "{#{$1.gsub('-', '_')}}" }
      dict[urlpath_pat] = DummyAPI
    end
  end
  mapping = {"/api" => dict}

  request_paths = [
    #'/gists/{gist_id}/star',
    '/gists/1234567890/star',
    #'/repos/{owner}/{repo}',
    '/repos/owner1/repo2',
    #'/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments',
    '/repos/owner1/repo2/pulls/333/reviews/444/comments',
    #'/teams/{team_id}/memberships/{username}',
    '/teams/12345/memberships/username1',
  ].collect {|x| "/api" + x }

  width = 75

else

  raise "#{benchdata}: unknown bench type."

end


N = Integer(ENV['N'] || 1000_000)

title = "router benchmark"
Benchmarker.scope(title, width: width, loop: 1, iter: nil, extra: nil) do
  ## other options -- inverse: true, outfile: "result.json", quiet: true,
  ##                  sleep: 1, colorize: true, filter: "task=*foo*"

  ## tasks
  task nil do    # empty-loop task
    n = N
    i = 0
    while (i += 1) <= n
      # do nothing
    end
  end

  router_classes.each do |router_class|
    request_paths.each do |request_path|
      #
      proc {|klass, req_path|
        router = klass.new(mapping)
        class_name = klass.name.sub(/Router/, '').sub(/^K8::/, '')
        label = "%-15s: %-16s" % [class_name, req_path]
        task label do
          req_path_ = req_path
          router_   = router
          n = N
          i = 0
          while (i += 1) <= n
            result = router_.find(req_path_)
          end
          result
        end
      }.call(router_class, request_path)
      #
    end
  end

  ## validation
  validate do |val, title|   # or: validate do |val, task_name, tag|
    case title.strip
    ## benchdata: "default"
    when /\/api\/aaa\/$/, /\/api\/zzz\/$/
      expected = [HelloAPI, {GET: :do_list, POST: :do_create}, []]
      assert_eq val, expected
    when /\/123\.json$/
      expected = [HelloAPI, {GET: :do_show, PUT: :do_update, DELETE: :do_delete}, [123]]
      assert_eq val, expected
    when /\/456\.json$/
      expected = [HelloAPI, {GET: :do_show, PUT: :do_update, DELETE: :do_delete}, [456]]
      assert_eq val, expected
    when /\/comments\/888\.json$/
      expected = [CommentAPI, {GET: :do_show, PUT: :do_update, DELETE: :do_delete}, [123, 888]]
      assert_eq val, expected
    when /\/comments\/999\.json$/
      expected = [CommentAPI, {GET: :do_show, PUT: :do_update, DELETE: :do_delete}, [456, 999]]
      assert_eq val, expected
    ## benchdata: "githubapi"
    when %r!/gists/1234567890/star$!
      expected = [DummyAPI, {GET: :do_nothing}, [1234567890]]
      assert_eq val, expected
    when %r!/api/repos/owner1/repo2$!
      expected = [DummyAPI, {GET: :do_nothing}, ["owner1", "repo2"]]
      assert_eq val, expected
    when %r!/api/repos/owner1/repo2/pulls/333/reviews/444/comments$!
      expected = [DummyAPI, {GET: :do_nothing}, ["owner1", "repo2", "333", 444]]
      assert_eq val, expected
    when %r!/api/teams/12345/memberships/username1$!
      expected = [DummyAPI, {GET: :do_nothing}, [12345, "username1"]]
      assert_eq val, expected
    else
      puts "** interal error: title=#{title.inspect}"
    end
  end

end
