
#!/usr/bin/python
"""Report errors with HTML emails that show everything necessary to debug."""

import time
import sys
import re
import os
import urllib2
import json
import socket
import threading
import webbrowser
import traceback

import memdam
import memdam.common.idebug
#NOTE: putting this here because you're pretty much guaranteed to import this file...
memdam.common.idebug.listen()

def report(e):
  exc_info = sys.exc_info()

  htmlContent = get_error_html(e, exc_info)
  textContent = '\n'.join(traceback.format_exception(*exc_info))

  memdam.log.error(textContent)
  if memdam.config.mandrill_key == None:
    filename = "/tmp/python_%s_%s_error.html" % \
               (os.getpid(), threading.current_thread().ident)
    html_file = open(filename, "wb")
    html_file.write(htmlContent)
    html_file.close()
    webbrowser.open_new_tab("file://%s" % (filename))
    #just so that it doesn't pop up a million windows
    sys.exit()
  else:
    send_email(memdam.config.mandrill_key, textContent, htmlContent)

def send_email(api_key, textContent, htmlContent=None, subject="remote error"):
  fromName = socket.gethostname()
  messageDict = {
      "subject": "myautoreporter " + subject,
      "from_email": "thejash@gmail.com",
      "from_name": fromName,
      "to": [
          {
              "email": "thejash@gmail.com"
          }
      ]
    }
  messageDict["text"] = textContent
  if htmlContent != None:
    messageDict["html"] = htmlContent
  jdata = json.dumps({
    "key": api_key,
    "message": messageDict
  })
  urllib2.urlopen("https://mandrillapp.com/api/1.0/messages/send.json", jdata)

def create_html_mail (sender, recipient, html, text, subject):
  """Create a mime-message that will render HTML in popular
  MUAs, text in better ones"""
  import MimeWriter
  import mimetools
  import cStringIO

  # output buffer for our message
  out = cStringIO.StringIO()
  htmlin = cStringIO.StringIO(html)
  txtin = cStringIO.StringIO(text)

  writer = MimeWriter.MimeWriter(out)

  # set up some basic headers... we put subject here
  # because smtplib.sendmail expects it to be in the
  # message body
  writer.addheader("Subject", subject)
  writer.addheader("MIME-Version", "1.0")
  writer.addheader("From", sender)
  writer.addheader("To", recipient)

  # start the multipart section of the message
  # multipart/alternative seems to work better
  # on some MUAs than multipart/mixed
  writer.startmultipartbody("alternative")
  writer.flushheaders()

  # the plain text section
  subpart = writer.nextpart()
  subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
  pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
  mimetools.encode(txtin, pout, 'quoted-printable')
  txtin.close()

  # start the html subpart of the message
  subpart = writer.nextpart()
  subpart.addheader("Content-Transfer-Encoding", "quoted-printable")

  # returns us a file-ish object we can write to
  pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
  mimetools.encode(htmlin, pout, 'quoted-printable')
  htmlin.close()

  # Now that we're done, close our writer and
  # return the message body
  writer.lastpart()
  msg = out.getvalue()
  out.close()
  return msg

def get_error_html(e, exc_info):
  import operator
  import cgi
  from pprint import pformat

  def escape(text):
    return cgi.escape(str(text))
  def pprint(value):
    try:
      return pformat(value)
    except Exception, e:
      return "Error in formatting: %s" % str(e)

  (exc_type, exc_value, tb) = exc_info
  frames = get_traceback_frames(tb)
  htmlBody = ""
  for frame in frames:
    varRowsHTML = ""
    sortedVars = sorted(frame['vars'], key=operator.itemgetter(0))
    #print sortedVars
    for varName, varValue in sortedVars:
      varRowsHTML += """
            <tr>
              <td>"""+escape(varName)+"""</td>
              <td class="code"><div>"""+escape(pprint(varValue))+"""</div></td>
            </tr>
          """
    preContextHTML = ""
    for line in frame['pre_context']:
      preContextHTML += "<li style='white-space:pre'>"+escape(line)+"</li>"

    postContextHTML = ""
    for line in frame['post_context']:
      postContextHTML += "<li style='white-space:pre'>"+escape(line)+"</li>"

    contextHTML = """
        <div class="context">
            <ol start=\""""+escape(frame['pre_context_lineno'])+"""\" class="pre-context"">
              """+preContextHTML+"""
            </ol>
            <ol start=\""""+escape(frame['lineno'])+"""\" class="context-line">
              <li style='white-space:pre'>"""+escape(frame['context_line'])+"""</li>
            </ol>
            <ol start=\""""+escape(int(frame['lineno'])+1)+"""\" class="post-context"">
              """+postContextHTML+"""
            </ol>
          </div>
    """
    htmlBody += """
    <li class="frame">
      <code>"""+escape(frame['filename'])+""":</code> in <code>"""+escape(frame['function'])+"""</code>
      """+contextHTML+"""
      <table class="vars"">
        <thead>
          <tr>
            <th>Variable</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          """+varRowsHTML+"""
        </tbody>
      </table>
    </li>
    <br/>
    <br/>
    <br/>
    <br/>
    <br/>

  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; }
    h2 { margin-bottom:.8em; }
    h2 span { font-size:80%; color:#666; font-weight:normal; }
    h3 { margin:1em 0 .5em 0; }
    h4 { margin:0 0 .5em 0; font-weight: normal; }
    table { border:1px solid #ccc; border-collapse: collapse; width:100%; background:white; }
    tbody td, tbody th { vertical-align:top; padding:2px 3px; }
    thead th { padding:1px 6px 1px 3px; background:#fefefe; text-align:left; font-weight:normal; font-size:11px; border:1px solid #ddd; }
    tbody th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    table.vars { margin:5px 0 2px 40px; }
    table.vars td, table.req td { font-family:monospace; }
    table td.code { width:100%; }
    table td.code div { overflow:hidden; }
    table.source th { color:#666; }
    table.source td { font-family:monospace; white-space:pre; border-bottom:1px solid #eee; }
    ul.traceback { list-style-type:none; }
    ul.traceback li.frame { margin-bottom:1em; }
    div.context { margin: 10px 0; }
    div.context ol { padding-left:30px; margin:0 10px; list-style-position: inside; }
    div.context ol li { font-family:monospace; white-space:pre; color:#666; cursor:pointer; }
    div.context ol.context-line li { color:black; background-color:#ccc; }
    div.context ol.context-line li span { float: right; }
    div.commands { margin-left: 40px; }
    div.commands a { color:black; text-decoration:none; }
    #summary { background: #ffc; }
    #summary h2 { font-weight: normal; color: #666; }
    #explanation { background:#eee; }
    #template, #template-not-exist { background:#f6f6f6; }
    #template-not-exist ul { margin: 0 0 0 20px; }
    #unicode-hint { background:#eee; }
    #traceback { background:#eee; }
    #requestinfo { background:#f6f6f6; padding-left:120px; }
    #summary table { border:none; background:transparent; }
    #requestinfo h2, #requestinfo h3 { position:relative; margin-left:-100px; }
    #requestinfo h3 { margin-bottom:-1em; }
    .error { background: #ffc; }
    .specific { color:#cc3300; font-weight:bold; }
    h2 span.commands { font-size:.7em;}
    span.commands a:link {color:#5E5694;}
    pre.exception_value { font-family: sans-serif; color: #666; font-size: 1.5em; margin: 10px 0 10px 0; }
  </style>
      """

  html = """
<html>
<head>
     <title>Error</title>
</head>
<body>
  <div style="width:500px">
    <h1>"""+escape(exc_type)+""" during backup</h1>
    <pre class="exception_value">"""+escape(exc_value)+"""</pre>
    <h2>Traceback:</h2>
    """+htmlBody+"""
  </div>
</body>
</html>
"""
  return html

def get_traceback_frames(tb):
  """Mostly take from Django, I like their tracebacks."""
  frames = []
  while tb is not None:
    # support for __traceback_hide__ which is used by a few libraries
    # to hide internal frames.
    if tb.tb_frame.f_locals.get('__traceback_hide__'):
        tb = tb.tb_next
        continue
    filename = tb.tb_frame.f_code.co_filename
    function = tb.tb_frame.f_code.co_name
    lineno = tb.tb_lineno - 1
    module_name = tb.tb_frame.f_globals.get('__name__')
    loader = tb.tb_frame.f_globals.get('__loader__')
    pre_context_lineno, pre_context, context_line, post_context = _get_lines_from_file(filename, lineno, 7, loader, module_name)
    if pre_context_lineno is not None:
        frames.append({
            'tb': tb,
            'filename': filename,
            'function': function,
            'lineno': lineno + 1,
            'vars': tb.tb_frame.f_locals.items(),
            'id': id(tb),
            'pre_context': pre_context,
            'context_line': context_line,
            'post_context': post_context,
            'pre_context_lineno': pre_context_lineno + 1,
        })
    tb = tb.tb_next

  if not frames:
    frames = [{
      'filename': '&lt;unknown&gt;',
      'function': '?',
      'lineno': '?',
      'context_line': '???',
    }]

  return frames

def _get_lines_from_file(filename, lineno, context_lines, loader=None, module_name=None):
  """
  Returns context_lines before and after lineno from file.
  Returns (pre_context_lineno, pre_context, context_line, post_context).
  """
  source = None
  if loader is not None and hasattr(loader, "get_source"):
    source = loader.get_source(module_name)
    if source is not None:
      source = source.splitlines()
  if source is None:
    try:
      f = open(filename)
      try:
        source = f.readlines()
      finally:
        f.close()
    except (OSError, IOError):
      pass
  if source is None:
    #return None, [], None, []
    return 0, [], "unknown", []

  encoding = 'ascii'
  for line in source[:2]:
    # File coding may be specified. Match pattern from PEP-263
    # (http://www.python.org/dev/peps/pep-0263/)
    match = re.search(r'coding[:=]\s*([-\w.]+)', line)
    if match:
      encoding = match.group(1)
      break
  source = [unicode(sline, encoding, 'replace') for sline in source]

  lower_bound = max(0, lineno - context_lines)
  upper_bound = lineno + context_lines

  pre_context = [line.strip('\n') for line in source[lower_bound:lineno]]
  context_line = source[lineno].strip('\n')
  post_context = [line.strip('\n') for line in source[lineno+1:upper_bound]]

  return lower_bound, pre_context, context_line, post_context
