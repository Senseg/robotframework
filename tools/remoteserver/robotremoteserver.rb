# Copyright 2008-2009 Nokia Siemens Networks Oyj
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


require 'xmlrpc/server'
require 'xmlrpc/utils'
require 'stringio'


class RobotRemoteServer < XMLRPC::Server
  
  def initialize(library, host='localhost', port=8270)
    @library = library
    super(port, host)  # TODO: Disable logging to stdout
    add_handler('get_keyword_names') { get_keyword_names }
    add_handler('run_keyword') { |name,args| run_keyword(name, args) }
    add_handler('get_keyword_arguments') { |name| get_keyword_arguments(name) }
    add_handler('get_keyword_documentation') { |name| get_keyword_documentation(name) }
    add_handler('stop_remote_server') { shutdown }
    puts "Robot Framework remote library started at #{host}:#{port}"
    serve
  end

  def get_keyword_names
    # Implicit methods can't be used as keywords
    @library.methods - Object.new.methods
  end

  def run_keyword(name, args)
    intercept_stdout()
    result = {:status=>'PASS', :return=>'', :output=>'',
              :error=>'', :traceback=>''}
    begin
      return_value = @library.send(name, *args)
      result[:return] = handle_return_value(return_value)
    rescue Exception => exception
      result[:status] = 'FAIL'
      result[:error] = exception.message
      result[:traceback] = "Traceback:\n" + exception.backtrace.join("\n")
    end
    result[:output] = restore_stdout
    return result
  end

  def get_keyword_arguments(name)
    # This algorithm doesn't return correct number of maximum arguments when 
    # args have default values. It seems that there's no easy way to get that
    # information in Ruby, see e.g. http://www.ruby-forum.com/topic/147614.
    # Additionally, it would be much better to return real argument names 
    # because that information could be used to create library documentation. 
    arity = @library.method(name).arity
    if arity >= 0
      return ['arg'] * arity
    else
      return ['arg'] * (arity.abs - 1) + ['*args']
    end
  end

  def get_keyword_documentation(name)  
    # Is there a way to implement this? Would mainly allow creating a library
    # documentation, but if real argument names are not got that's probably
    # not so relevant.
    ''
  end

  private

  def handle_return_value(ret)
    if [String, Integer, Fixnum, Float, TrueClass, FalseClass].include?(ret.class)
      return ret
    elsif ret.class == Array
      return ret.collect { |item| handle_return_value(item) }
    elsif ret.class == Hash
      new_ret = {}
      ret.each_pair { |key,value|
        new_ret[key.to_s] = handle_return_value(value)
      }
      return new_ret
    else
      return ret.to_s
    end
  end

  def intercept_stdout
    $original_stdout = $stdout.dup
    @output = ''
    $stdout = StringIO.new(@output)
  end
  
  def restore_stdout
    $save_for_close = $stdout
    $stdout = $original_stdout
    $save_for_close.close
    return @output
  end
    
end
