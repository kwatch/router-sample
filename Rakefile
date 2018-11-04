

task :default => :test

task :test do
  sh "python3 -m oktest tests"
end


FILENAME = "List_of_HTTP_status_codes"

file FILENAME do
  url = "https://en.wikipedia.org/wiki/List_of_HTTP_status_codes"
  sh "curl -O #{url}"
end

def parse(filename, separator=nil, comment='#', &blk)
  if block_given?
    _parse(filename, &blk)
  else
    prev = 0; c = nil
    puts "{"
    _parse(filename) do |status_code, status_msg, note|
      c = comment if c.nil? && prev > status_code
      msg = "\"#{status_msg}\","
      s = note.nil? ? msg : "%-35s #{comment} %s" % [msg, note]
      puts "  #{c}#{status_code}#{separator}#{s}"
      prev = status_code
    end
    puts "}"
  end
end

def _parse(filename, &blk)
  str = File.read(filename)
  rexp = /<dt>(?:<span id="\d\d\d(?:-.*?)?"><\/span>)?(.*?)<\/dt>/
  str.scan(rexp).each do |text,|
    text = text.gsub(/<a .*?>/, '').gsub(/<\/a>/, '')
    text =~ /\A(\d\d\d) (.*?)(\(.*\))?$/ or
      raise "Failed: text=#{text.inspect}"
    status_code = $1.to_i
    status_msg  = $2.strip
    note        = $3
    yield status_code, status_msg, note
  end
end

namespace :status do

  desc "list status code in YAML format"
  task :yaml => FILENAME do
    parse(FILENAME) {|status_code, status_msg, note|
      note_val = note ? "\"#{note}\"" : "null"
      puts %Q`- {"code": #{status_code}, "message": "#{status_msg}", "note": #{note_val}}`
    }
  end

  desc "list status code in JSON format"
  task :json => FILENAME do
    puts "["
    s = "  "
    parse(FILENAME) do |status_code, status_msg, note|
      note_val = note ? "\"#{note}\"" : "null"
      if note
        puts %Q`#{s}{"code": #{status_code}, "message": "#{status_msg}", "note": "#{note}"}`
      else
        puts %Q`#{s}{"code": #{status_code}, "message": "#{status_msg}"}`
      end
      s = ", "
    end
    puts "]"
  end

  desc "list status code in Ruby hash"
  task :ruby => FILENAME do
    parse(FILENAME, " => ", "#")
  end

  desc "list status code in Python dict"
  task :python => FILENAME do
    parse(FILENAME, ": ", "#")
  end

  desc "list status code in JavaScript object"
  task :javascript => FILENAME do
    parse(FILENAME, ": ", "//")
  end

end
