# coding: utf-8

require 'oktest'
require_relative '../../minikeight'


class HelloHandler < K8::RequestHandler
  mapping "/"          , :GET=>:do_index, :POST=>:do_create
  mapping "/new"       , :GET=>:do_new
  mapping "/{id}.json" , :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping "/{id}/edit" , :GET=>:do_edit
  def do_index()   ; {action: "index"}         ; end
  def do_create()  ; {action: "create"}        ; end
  def do_new()     ; {action: "new"}           ; end
  def do_show(id)  ; {action: "show", id: id}  ; end
  def do_update(id); {action: "update", id: id}; end
  def do_delete(id); {action: "delete", id: id}; end
  def do_edit(id)  ; {action: "edit", id: id}  ; end
end

class CommentHandler < K8::RequestHandler
  mapping "/"          , :GET=>:do_index, :POST=>:do_create
  mapping "/new"       , :GET=>:do_new
  mapping "/{id}.json" , :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
  mapping "/{id}/edit" , :GET=>:do_edit
  def do_index(x_id)   ; {action: "index"}         ; end
  def do_create(x_id)  ; {action: "create"}        ; end
  def do_new(x_id)     ; {action: "new"}           ; end
  def do_show(x_id, comment_id)  ; {action: "show", id: id}  ; end
  def do_update(x_id, comment_id); {action: "update", id: id}; end
  def do_delete(x_id, comment_id); {action: "delete", id: id}; end
  def do_edit(x_id, comment_id)  ; {action: "edit", id: id}  ; end
end

class AnyHandler < K8::RequestHandler
  mapping "" ,:GET=>:do_nothing
  def do_nothing(*args)
    return {args=>args}
  end
end

mapping1 = {
  "/api/v1" => {
    "/hello" => HelloHandler,
    "/hello/{x_id}/comments" => CommentHandler,
    "/helloworld" => HelloHandler,
  },
  ##
  "/repos/{owner}/{repo}" => {
    "/git/blobs" => AnyHandler,
    "/pulls/{pull_number}/reviews/{review_id}/comments" => AnyHandler,
    "/generate" => AnyHandler,
  },
}
mapping2 = {
  "/api/v2" => {
    "/hello" => {
      "" => HelloHandler,
      "/{x_id}/comments" => CommentHandler,
      "world" => HelloHandler,
    }
  },
  ##
  "/repos/{owner}" => {
    "/{repo}" => {
      "/git/blobs" => AnyHandler,
      "/pulls/{pull_number}" => {
        "/reviews/{review_id}/comments" => AnyHandler,
      },
      "/generate" => AnyHandler,
    },
  },
}

router_classes = [
  K8::NaiveLinearRouter,
  K8::PrefixLinearRouter,
  K8::FixedLinearRouter,
  K8::HashedLinearRouter,
  K8::NaiveRegexpRouter,
  K8::SmartRegexpRouter,
  K8::NestedRegexpRouter,
  K8::OptimizedRegexpRouter,
  K8::SlicedRegexpRouter,
  K8::HashedRegexpRouter,
  K8::ListBasedTrieRouter,
  K8::DictBasedTrieRouter,
  K8::StateMachineRouter,
  K8::NestedDictRouter,
]


Oktest.scope do

  maketestcases = proc do |klass, mapping, ver|

    topic klass do

      router = klass.new(mapping)

      topic '#find()' do

        spec "/api/#{ver}/hello/" do
          ret = router.find("/api/#{ver}/hello/")
          methods = {:GET=>:do_index, :POST=>:do_create}
          ok {ret} == [HelloHandler, methods, []]
        end

        spec "/api/#{ver}/hello/new" do
          ret = router.find("/api/#{ver}/hello/new")
          methods = {:GET=>:do_new}
          ok {ret} == [HelloHandler, methods, []]
        end

        spec "/api/#{ver}/hello/123.json" do
          ret = router.find("/api/#{ver}/hello/123.json")
          methods = {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}
          ok {ret} == [HelloHandler, methods, [123]]
        end

        spec "/api/#{ver}/hello/123/edit" do
          ret = router.find("/api/#{ver}/hello/123/edit")
          methods = {:GET=>:do_edit}
          ok {ret} == [HelloHandler, methods, [123]]
        end

        spec "/api/#{ver}/hello/123/comments/" do
          ret = router.find("/api/#{ver}/hello/123/comments/")
          methods = {:GET=>:do_index, :POST=>:do_create}
          ok {ret} == [CommentHandler, methods, [123]]
        end

        spec "/api/#{ver}/hello/123/comments/{id}.json" do
          ret = router.find("/api/#{ver}/hello/123/comments/888.json")
          methods = {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}
          ok {ret} == [CommentHandler, methods, [123, 888]]
        end

        spec "/api/#{ver}/helloworld/" do
          ret = router.find("/api/#{ver}/helloworld/")
          methods = {:GET=>:do_index, :POST=>:do_create}
          ok {ret} == [HelloHandler, methods, []]
        end

        spec "/api/#{ver}/helloworld/123.json" do
          ret = router.find("/api/#{ver}/helloworld/123.json")
          methods = {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete}
          ok {ret} == [HelloHandler, methods, [123]]
        end

        ##

        spec "/repos/owner1/repo2/pulls/333/reviews/444/comments" do
          ret = router.find("/repos/owner1/repo2/pulls/333/reviews/444/comments")
          methods = {:GET=>:do_nothing}
          ok {ret} == [AnyHandler, methods, ["owner1", "repo2", "333", 444]]
        end

      end

    end

  end

  router_classes.each do |router_class|
    {"v1" => mapping1, "v2" => mapping2}.each do |ver, mapping|
      maketestcases.call(router_class, mapping, ver)
    end
  end

end
