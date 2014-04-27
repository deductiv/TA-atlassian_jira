import splunk.Intersplunk
import time
import urllib2
import re
import splunk.clilib.cli_common as spcli
import base64
import json
import urllib
import sys
import collections

row={}
results=[]
keywords, options = splunk.Intersplunk.getKeywordsAndOptions()
creds= spcli.getConfStanza("jirauser","jirauser")
auth =creds['user']+":"+creds['pass']
authencode=base64.b64encode(auth)
pattern = '%Y-%m-%dT%H:%M:%S'
datepattern="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
datevalues=re.compile(datepattern)
option=sys.argv[1]


if option == 'filters':
    target = "https://jira.splunk.com/rest/api/2/filter/favourite?expand"
    reqf = urllib2.Request(target)
    reqf.add_header('Content-Type', 'application/json; charset=utf-8')
    reqf.add_header('Authorization', 'Basic '+authencode )
    filters = urllib2.urlopen(reqf)
    for filter in json.load(filters):
       
        row['name']=filter['name']
        row['id']=filter['id']
        row['owner']=filter['owner']['name']
        row['owner_name']=filter['owner']['displayName']
        row['search']=filter['jql']
        row['url']=filter['viewUrl']
        row['_time'] = int(time.time())
        row['_raw'] = row
        results.append(row)
        row={}
    splunk.Intersplunk.outputStreamResults(results)
    results=[]
    exit()

if option == 'rapidboards':
   args=sys.argv[2]
   if args=="all":
     target="https://jira.splunk.com/rest/greenhopper/1.0/rapidviews/list"
   elif args=="list":
     target="https://jira.splunk.com/rest/greenhopper/1.0/rapidview"
   else:
     target="https://jira.splunk.com/rest/greenhopper/1.0/rapidview/"+args
   reqrb = urllib2.Request(target)
   reqrb.add_header('Content-Type', 'application/json; charset=utf-8')
   reqrb.add_header('Authorization', 'Basic '+authencode )
   rbopen = urllib2.urlopen(reqrb)
   rapidboards= json.load(rbopen)
   rbamv=[]
   if args!="all":
     if args=="list":
       for view in rapidboards['views']:
        row['name']=view['name']
        row['id']=view['id']
        row['source'] = option
        row['host'] = "JIRA"
        row['sourcetype'] = "JIRA_Search"
        row['_time'] = int(time.time())
        row['_raw'] = row
        results.append(row)
        row={}
       splunk.Intersplunk.outputStreamResults(results)
       results=[]
       exit()
     target2="https://jira.splunk.com/rest/greenhopper/1.0/sprintquery/"+str(rapidboards['id'])+"?includeHistoricSprints=true&includeFutureSprints=true"
     reqsp = urllib2.Request(target2)
     reqsp.add_header('Content-Type', 'application/json; charset=utf-8')
     reqsp.add_header('Authorization', 'Basic '+authencode )
     sprintopen = urllib2.urlopen(reqsp)
     sprints= json.load(sprintopen)
     for sprint in sprints['sprints']:
        row['name']=rapidboards['name']
        row['id']=rapidboards['id']
        row['sprint_id']=sprint['id']
        row['sprint_name']=sprint['name']
        row['sprint_state']=sprint['state']
        row['source'] = option
        row['host'] = "JIRA"
        row['sourcetype'] = "JIRA_Search"
        row['_time'] = int(time.time())
        row['_raw'] = row
        results.append(row)
        row={}
        splunk.Intersplunk.outputStreamResults(results)
        results=[]
   else:
     for view in rapidboards['views']:
      target2="https://jira.splunk.com/rest/greenhopper/1.0/sprintquery/"+str(view['id'])+"?includeHistoricSprints=true&includeFutureSprints=true"
      reqsp = urllib2.Request(target2)
      reqsp.add_header('Content-Type', 'application/json; charset=utf-8')
      reqsp.add_header('Authorization', 'Basic '+authencode )
      sprintopen = urllib2.urlopen(reqsp)
      sprints= json.load(sprintopen)
      for sprint in sprints['sprints']:
        row['sprint_id']=sprint['id']
        row['sprint_name']=sprint['name']
        row['sprint_state']=sprint['state']
        row['_time'] = int(time.time())
        row['source'] = option
        row['host'] = "JIRA"
        row['sourcetype'] = "JIRA_Search"
        row['_time'] = int(time.time())
        row['_raw'] = row
        row['name']=view['name']
        row['id']= view['id']
        row['owner']=view['filter']['owner']['userName']
        row['owner_name']= view['filter']['owner']['displayName']
        row['filter_query']= view['filter']['query']
        row['filter_name']= view['filter']['name']
        row['filter_id']=view['filter']['id']
        for admin in view['boardAdmins']['userKeys']:
           rbamv.append(admin['key'])
        row['boardAdmins']=rbamv
        row['_time'] = int(time.time())
        row['_raw'] = row
        results.append(row)
        row={}
        rbamv=[]
      splunk.Intersplunk.outputStreamResults(results)
      results=[]
   exit()



if option == 'changelog':
   target = "https://jira.splunk.com/rest/api/2/search?jql="
   args=sys.argv[2].split()
   querystring= '+'.join(args)
   clfieldmv=[]
   clfrommv=[]
   cltomv=[]
   reqcl = urllib2.Request(target+querystring+"&fields=key,id,reporter,assignee,summary&maxResults=1000&expand=changelog&validateQuery=false")
   reqcl.add_header('Content-Type', 'application/json; charset=utf-8')
   reqcl.add_header('Authorization', 'Basic '+authencode )
   clopen = urllib2.urlopen(reqcl)
   changelog= json.load(clopen)
   for issue in changelog['issues']:
      for field in issue['changelog']['histories']:
         for item in field['items']:
           row['created']=field['created']
           row['user']=field['author']['name']
           row['user_name']=field['author']['displayName']
           row['field']=item['field']
           row['from']=item['fromString']
           row['to']=item['toString']
           if datevalues.match(row['created']):
               jdate= datevalues.match(row['created']).group(1)
           epoch = int(time.mktime(time.strptime(jdate, pattern)))
           row['_time'] = epoch
           row['_raw'] = row
           row['source'] = option
           row['host'] = "JIRA"
           row['sourcetype'] = "JIRA_Search"
           row['key']=issue['key']
           if issue['fields']['reporter']==None:
               row['reporter']=None
               row['reporter_name']=None
           else:
               row['reporter']=issue['fields']['reporter']['name']
               row['reporter_name']=issue['fields']['reporter']['displayName']
           if issue['fields']['assignee']==None:
               row['assignee']=None
               row['assignee_name']=None
           else:
               row['assignee']=issue['fields']['assignee']['name']
               row['assignee_name']=issue['fields']['assignee']['displayName']
           row['summary']=issue['fields']['summary']
           results.append(row)
           row={}
         splunk.Intersplunk.outputStreamResults(results)
         results=[]
   exit()

if "changefield" in sys.argv[3:]:
   changefield=True  
else:
   changefield=False
if "comments" in sys.argv[3:]:
   comments=True
else:
   comments=False
if "changetime" in sys.argv[3:]:
    timestamp=sys.argv[sys.argv.index("changetime")+1]
else:
    timestamp="created"






def main(changefield,comments,timestamp):
  global issuecount
  try: 
    row={}
    results=[]
    affectsmv=[]
    fixesmv=[]
    fieldlist={}
    flist=[]
    linkedmv=[]
    linkedstatusmv=[]
    linkedprioritymv=[]
    linkedsummarymv=[]
    linkedtypemv=[]
    fields=""
    componentsmv=[]
    try: issuecount
    except: issuecount=0  
    if issuecount>=1000:
       offset="&startAt="+str(issuecount)
    else:
       offset=""
    if option == 'jqlsearch':
        args=sys.argv[2].split()
        if len(sys.argv)>3 and "fields" in sys.argv[3:]:
           fields="&fields=key,id,created,"+sys.argv[sys.argv.index('fields')+1]
        target = "https://jira.splunk.com/rest/api/2/search?jql="
        querystring= '+'.join(args)
        if comments==True:
          req = urllib2.Request(target+querystring+"&maxResults=10000&fields=key"+offset+"&validateQuery=false")
        else:
          req = urllib2.Request(target+querystring+"&maxResults=10000"+fields+offset+"&validateQuery=false")

    if option == 'batch':
        args=sys.argv[2].split()
        batchargs=sys.argv[3]
        if len(sys.argv)>4 and "fields" in sys.argv[4:]:
           fields="&fields=key,id,created,"+sys.argv[sys.argv.index('fields')+1]
        batchargs=re.sub(',',' ',batchargs)
        batchargs=batchargs.split()
        batchargs=','.join(batchargs)
        target = "https://jira.splunk.com/rest/api/2/search?jql="
        querystring= '+'.join(args)+"("+batchargs+")"
        if comments==True:
          req = urllib2.Request(target+querystring+"&maxResults=10000&fields=key"+offset+"&validateQuery=false")
        else:
          req = urllib2.Request(target+querystring+"&maxResults=10000"+fields+offset+"&validateQuery=false")


    if option == 'issues':
        args=sys.argv[2]
        if len(sys.argv)>3 and "fields" in sys.argv[3:]:
           fields="&fields=key,id,created,"+sys.argv[sys.argv.index('fields')+1]
        target = "https://jira.splunk.com/rest/api/2/search?jql=filter="+args
        if comments==True:
          req = urllib2.Request(target+"&maxResults=10000&fields=key"+offset+"&validateQuery=false")
        else:
           req = urllib2.Request(target+"&maxResults=10000"+fields+offset+"&validateQuery=false")

    fieldtarget = "https://jira.splunk.com/rest/api/2/field"
    fieldreq = urllib2.Request(fieldtarget)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    fieldreq.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Authorization', 'Basic '+authencode )
    fieldreq.add_header('Authorization', 'Basic '+authencode )
    fields = urllib2.urlopen(fieldreq)
    handle=urllib2.urlopen(req)
    fullfields=json.load(fields)
    full2=json.load(handle)
    if comments==True:
      for issue in full2['issues']:
           commenttarget = "https://jira.splunk.com/rest/api/2/issue/"+issue['key']+"/comment"
           reqc = urllib2.Request(commenttarget)
           reqc.add_header('Content-Type', 'application/json; charset=utf-8')
           reqc.add_header('Authorization', 'Basic '+authencode )
           commentf = urllib2.urlopen(reqc)
           commentfull=json.load(commentf)['comments']
           for comment in commentfull:
              for author in comment:
                 if author=="author" or author=="updateAuthor":
                   row[author]=comment[author]['name']
                   row[author+"_name"]=comment[author]['displayName']
              row['created']=comment['created']
              row['updated']=comment['updated']
              row['comment']=comment['body']
              if changefield==True:
                row['key']=issue['key']
              else:
                row['Key']=issue['key']
              if row[timestamp]!=None:
                 if datevalues.match(row[timestamp]):
                    jdate= datevalues.match(row[timestamp]).group(1)
                    epoch = int(time.mktime(time.strptime(jdate, pattern)))
              else:
                 epoch=0
              row['_time'] = epoch
              row['_raw'] = row
              row['source'] = option
              row['host'] = "JIRA"
              row['sourcetype'] = "JIRA_Search"
              results.append(row)
              row={}
           splunk.Intersplunk.outputStreamResults(results)
           results=[]
      exit() 
    for fielditem in fullfields:
      fieldlist[fielditem['id']] = fielditem['name']
      flist.append(fieldlist)
    for issue in full2['issues']:
       for jirafield in issue['fields']:
           if changefield==True:
             field=jirafield
           else:
              if jirafield in fieldlist:
                field=fieldlist[jirafield]
              else:
                field= jirafield
           if issue['fields'][jirafield]==None:
              row[field]=None
           elif (isinstance(issue['fields'][jirafield], basestring)==True):
                row[field]=issue['fields'][jirafield]
                if field=='Labels':
                  row[field]=issue['fields'][jirafield]
           elif (isinstance(issue['fields'][jirafield], collections.Iterable)==True):
                for mvfield1 in issue['fields'][jirafield]:
                   if (isinstance(mvfield1, basestring)==True):
                    if mvfield1=='name' or mvfield1=='value' or mvfield1=='displayName':
                       if mvfield1=='displayName':
                          row[field+"_"+"Name"]=issue['fields'][jirafield][mvfield1]
                       else:
                          row[field]=issue['fields'][jirafield][mvfield1]
                   else:
                     if (isinstance(mvfield1, collections.Iterable)==True):
                        for mvfield2 in mvfield1:
                         if (isinstance(mvfield2, basestring)==True):
                             if mvfield2=='name' or mvfield2=='value' or mvfield2=='displayName': 
                               if jirafield=='versions': 
                                 affectsmv.append(mvfield1[mvfield2])
                               elif jirafield=='fixVersions':
                                 fixesmv.append(mvfield1[mvfield2])
                               elif jirafield=='components':
                                 componentsmv.append(mvfield1[mvfield2])
                               else:
                                 row[field]=mvfield1[mvfield2]   
                                     
                             elif mvfield2=='inwardIssue' or mvfield2=='outwardIssue':
                               for mvfield3 in mvfield1[mvfield2]:
                                  if mvfield3=='key':
                                    linkedmv.append(mvfield1[mvfield2][mvfield3])
                                    if mvfield2=="inwardIssue":
                                       linkedtypemv.append(mvfield1['type']['inward']+"-"+mvfield1[mvfield2][mvfield3])
                                    if mvfield2=="outwardIssue":
                                       linkedtypemv.append(mvfield1['type']['outward']+"-"+mvfield1[mvfield2][mvfield3])
                                    linkedsummarymv.append(mvfield1[mvfield2][mvfield3]+"-"+mvfield1[mvfield2]['fields']['summary'])
                                    linkedstatusmv.append(mvfield1[mvfield2][mvfield3]+"-"+mvfield1[mvfield2]['fields']['status']['name'])
                                    linkedprioritymv.append(mvfield1[mvfield2][mvfield3]+"-"+mvfield1[mvfield2]['fields']['priority']['name'])
           else:
              row[field]=str(issue['fields'][jirafield])
       
       if changefield!=True:
          if row[fieldlist[timestamp]]!=None:
             if datevalues.match(row[fieldlist[timestamp]]):
                jdate= datevalues.match(row[fieldlist[timestamp]]).group(1)
                epoch = int(time.mktime(time.strptime(jdate, pattern)))
          else:
             epoch=0
          if affectsmv!=[]:
            row['Affects Version/s']=affectsmv
          if fixesmv!=[]:
            row['Fix Version/s']=fixesmv
          if linkedmv!=[]:
            row['Linked']=linkedmv
          if linkedstatusmv!=[]:
            row['Linked_status']=linkedstatusmv
          if linkedprioritymv!=[]:
            row['Linked_priority']=linkedprioritymv
          if linkedsummarymv!=[]:
            row['Linked_summary']=linkedsummarymv
          if linkedtypemv!=[]:
            row['Linked_type']=linkedtypemv
          if componentsmv!=[]:
            row['Component/s']=componentsmv

       else:
          if row[timestamp]!=None:
              if datevalues.match(row[timestamp]):
                jdate= datevalues.match(row[timestamp]).group(1)
                epoch = int(time.mktime(time.strptime(jdate, pattern)))
          else:
             epoch=0
          if affectsmv!=[]:
            row['versions']=affectsmv
          if fixesmv!=[]:
            row['fixVersions']=fixesmv
          if linkedmv!=[]:
            row['issuelinks']=linkedmv
          if linkedstatusmv!=[]:
            row['issuelinks_status']=linkedstatusmv
          if linkedprioritymv!=[]:
            row['issuelinks_priority']=linkedprioritymv
          if linkedsummarymv!=[]:
            row['issuelinks_summary']=linkedsummarymv
          if linkedtypemv!=[]:
            row['issuelinks_type']=linkedtypemv
          if componentsmv!=[]:
            row['components']=componentsmv




       if changefield==True: 
         row['key']=issue['key']
       else:
         row['Key']=issue['key']
       row['_time'] = epoch
       row['_raw'] = row
       row['source'] = option
       row['host'] = "JIRA"
       row['sourcetype'] = "JIRA_Search"
       results.append(row)     
       row={}
       fixesmv=[]
       affectsmv=[]
       linkedstatusmv=[]
       linkedmv=[]
       linkedprioritymv=[]
       linkedsummarymv=[]
       linkedtypemv=[]
       componentsmv=[]
    splunk.Intersplunk.outputStreamResults(results)
    results=[]
    issuecount=issuecount+len(full2['issues'])
    if int(len(full2['issues']))>=1000:
      main(changefield,comments,timestamp)       
    else:
      exit()
       
    


   

  except Exception, e:
        import traceback
        results=[]
        row={}
        stack =  traceback.format_exc()
        row['_time'] = int(time.time())
        row['error'] = str(str(e))
        row['search']= " ".join(args)
        results.append(row)
        splunk.Intersplunk.outputStreamResults(results)



main(changefield,comments,timestamp)