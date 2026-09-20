from flask import Flask, render_template, jsonify, request
import json, os, re, requests

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(name, default):
    try:
        with open(os.path.join(DATA_DIR,name), encoding="utf-8") as f: return json.load(f)
    except Exception as e:
        print(f"Could not load {name}: {e}"); return default

college_info = load_json("college_info.json", {})
departments_data = load_json("departments.json", {"departments":[]})
official_data = load_json("official_data.json", {"pages":[]})

def departments(): return departments_data.get("departments",[]) if isinstance(departments_data,dict) else departments_data

def norm(s):
    s=str(s or "").lower().strip()
    for a,b in {"cse (aiml)":"aiml","cse aiml":"aiml","cse(a iml)":"aiml","kon aahe":"who","kon":"who","cha":"of","chi":"of","madhe":"in","ahe":"is","aahet":"are","sang":"tell"}.items(): s=s.replace(a,b)
    return re.sub(r"\s+"," ",s)

def find_department(q):
    n=norm(q)
    for d in departments():
        aliases=[d.get("name","")]+d.get("aliases",[])
        for a in aliases:
            if a and norm(a) in n: return d
    return None

def exact_answer(q):
    n=norm(q)
    # Exact college leadership facts first. Never send these to an LLM.
    if any(x in n for x in ["chairman","chair man","chairperson"]):
        return f"👤 Chairman\n\nPravin Pote Patil\n\nSource: {college_info['about_url']}"
    if any(x in n for x in ["vice chairman","vice-chairman","vice chair man"]):
        return f"👤 Vice Chairman\n\nShreyash Pote Patil\n\nSource: {college_info['about_url']}"
    if "principal" in n and "vice principal" not in n:
        return f"🎓 Principal\n\n{college_info['principal']}\n\nSource: {college_info['about_url']}"
    if "vice principal" in n or "vice-principal" in n:
        return f"🎓 Vice Principal\n\n{college_info['vice_principal']}\n\nSource: {college_info['about_url']}"
    if "director" in n:
        return f"🏛️ Director\n\n{college_info['director']}\n\nSource: {college_info['about_url']}"
    if any(x in n for x in ["hod","head of","department head"]):
        d=find_department(q)
        if d and d.get('hod'): return f"👨‍🏫 HOD — {d['name']}\n\n{d['hod']}\n\nSource: {d.get('source',college_info['official_website'])}"
    if any(x in n for x in ["departments","department list","branches","branches available","all branches"]):
        return "🏫 Departments at P. R. Pote Patil College of Engineering & Management\n\n"+"\n".join(f"{i}. {d['name']}" for i,d in enumerate(departments(),1))
    if any(x in n for x in ["facility","facilities","infrastructure"]):
        return "🏢 College Facilities\n\n"+"\n".join("• "+x for x in college_info.get('facilities',[]))
    if "address" in n or "location" in n: return f"📍 Address\n\n{college_info['address']}"
    if "established" in n or "when was college" in n: return f"📅 Established: {college_info['established']}"
    d=find_department(q)
    if d and any(x in n for x in ["intake","seats","capacity","degree","course","program","programme","duration"]):
        lines=[f"🎓 {d['name']}"]
        if d.get('degree'): lines.append(f"Degree: {d['degree']}")
        if d.get('duration'): lines.append(f"Duration: {d['duration']}")
        if d.get('intake'): lines.append(f"Intake: {d['intake']}")
        return "\n\n".join(lines)
    if any(x in n for x in ["about college","college details","college information"]):
        return f"🏫 {college_info['college_name']}\n\n📍 {college_info['address']}\n📅 Established: {college_info['established']}\n🏛️ {college_info['status']}"
    if "library" in n: return "📖 Library is one of the facilities listed by the college. For current library services/timings, check the official college website."
    if "exam" in n or "examination" in n or "ese" in n: return "📝 The official Examination Cell publishes current examination notices, timetables and related information.\n\nExam Cell: https://examcell.prpotepatilengg.ac.in/"
    if "syllabus" in n or "scheme" in n: return "📘 Syllabus and scheme documents are published through the college academic resources. Please specify your branch and semester for a targeted answer."
    if "faculty" in n or "teacher" in n or "professor" in n:
        d=find_department(q)
        if d: return f"👨‍🏫 Faculty for {d['name']} is available on its official department page.\n\nI will not invent faculty names. Please use the official department page: {d.get('source',college_info['official_website'])}"
        return "👨‍🏫 Tell me the department, for example: AIML faculty or CSE faculty."
    return None

def search_official(q):
    pages=official_data.get('pages',[]) if isinstance(official_data,dict) else []
    words=[w for w in norm(q).split() if len(w)>2]
    scored=[]
    for p in pages:
        txt=(str(p.get('title',''))+' '+' '.join(map(str,p.get('content',[])))).lower(); score=sum((3 if w in str(p.get('title','')).lower() else 0)+(1 if w in txt else 0) for w in words)
        if score: scored.append((score,p))
    return [p for _,p in sorted(scored,key=lambda x:x[0],reverse=True)[:3]]

def gemini_answer(q):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key: return None
    model=os.getenv('GEMINI_MODEL','gemini-3.5-flash').strip()
    context=json.dumps({'college':college_info,'departments':departments()},ensure_ascii=False)
    prompt=("You are POTE AI, the college assistant. Answer only from the supplied verified college data. "
            "Never invent names, fees, dates, faculty, rules or schedules. If the data does not contain the answer, say that it is not available. "
            "Be concise and directly answer the student's question.\n\nVERIFIED DATA:\n"+context+"\n\nQUESTION: "+q)
    try:
        r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",json={'contents':[{'parts':[{'text':prompt}]}]},timeout=25)
        if r.ok:
            parts=r.json().get('candidates',[{}])[0].get('content',{}).get('parts',[])
            if parts: return parts[0].get('text','').strip() or None
        print('Gemini API:',r.status_code,r.text[:500])
    except Exception as e: print('Gemini error:',e)
    return None

def answer_question(q):
    n=norm(q)
    if n in {'hi','hello','hey','namaste','good morning','good evening','good afternoon'}:
        return "Hello! 👋 I am P.R. Pote AI. Ask me about departments, HODs, leadership, courses, facilities, faculty, exams and college information."
    a=exact_answer(q)
    if a: return a
    results=search_official(q)
    if results:
        p=results[0]; content=p.get('content',[])
        return "🔎 Information found in collected official data:\n\n"+"\n".join('• '+str(x) for x in content[:8])+f"\n\nSource: {p.get('url','')}"
    a=gemini_answer(q)
    if a: return a
    return "I don't have a verified answer for that yet, so I won't guess. Please ask about the college, departments, HODs, leadership, courses, facilities, faculty or exams."

@app.route('/')
def home(): return render_template('index.html')
@app.route('/api/college')
def api_college(): return jsonify(college_info)
@app.route('/api/departments')
def api_departments(): return jsonify(departments())
@app.route('/api/official')
def api_official(): return jsonify(official_data)
@app.route('/api/ask',methods=['POST'])
def ask():
    data=request.get_json(silent=True) or {}; q=str(data.get('question','')).strip()
    return jsonify({'answer':answer_question(q) if q else 'Please type or speak your question.'})

if __name__=='__main__': app.run(debug=True)
