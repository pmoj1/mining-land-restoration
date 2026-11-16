from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
D=Document(); s=D.sections[0]; s.page_height=Inches(11.7);s.page_width=Inches(8.3)
s.top_margin=s.bottom_margin=Inches(.7);s.left_margin=s.right_margin=Inches(.75)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 st=D.styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
D.styles['Normal'].font.size=Pt(11);D.styles['Normal'].paragraph_format.space_after=Pt(7)
D.styles['Normal'].paragraph_format.line_spacing=1.08
D.styles['Title'].font.size=Pt(27)
D.styles['Heading 1'].font.size=Pt(17);D.styles['Heading 2'].font.size=Pt(12)
def p(t,style=None):return D.add_paragraph(t,style)
def h(t):D.add_heading(t,1)
def bullet(t):p(t,'List Bullet')
def table(headers,rows,widths):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 for c,v in zip(t.rows[0].cells,headers):c.text=v
 rep=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(rep)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=v
 for i,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();ns=OxmlElement('w:cantSplit');pr.append(ns)
  for cell in row.cells:
   cp=cell._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'17364D' if i==0 else ('F2F5F7' if i%2==0 else 'FFFFFF'));cp.append(sh)
   borders=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
   cp.append(borders)
   margins=OxmlElement('w:tcMar')
   for side in ['top','left','bottom','right']:
    m=OxmlElement('w:'+side);m.set(qn('w:w'),'100');m.set(qn('w:type'),'dxa');margins.append(m)
   cp.append(margins)
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(3)
    for r in para.runs:
     r.font.size=Pt(10)
     if i==0:r.font.bold=True;r.font.color.rgb=RGBColor(255,255,255)
 return t
p('Mining Rehabilitation Research Prototype','Title')
p('Joint project plan for you and Kevin','Subtitle')
p('14 October 2026  |  Start after Atlas IQ')
h('Purpose and first deliverable')
p('Build a prototype that connects observable land changes at a mine with transparent rehabilitation spending scenarios. Use Nyanzaga in Tanzania as the first case study, with a structure that can later support other mines.')
p('The first deliverable is an interactive map, a simple financial model, and a short demonstration. Users compare imagery from two dates, inspect reviewed areas of change, and explore how cost assumptions, inflation, and rehabilitation timing affect estimated spending.')
h('What makes the concept useful')
p('The proposed contribution is the connection between physical evidence and financial planning. Satellite monitoring already exists. We will investigate whether combining it with an inspectable scenario model addresses a useful gap for mining finance teams. We will not claim the concept is unique or that Perseus lacks similar internal tools.')
h('Responsibilities')
table(['You with ChatGPT','Kevin with Claude'],[
('Own the application and final integration.','Own imagery research and economic scenarios.'),
('Research disclosures, accounting treatment, and financial inputs.','Locate the site and assess image coverage, dates, and quality.'),
('Build and check the cash flow and cost model.','Produce reviewed land change measurements and uncertainty notes.'),
('Build scenario controls and prepare the final demo.','Research inflation and cost assumptions; review map interpretations.')],[3.4,3.4])
p('Both partners review each other’s work. These are proposed roles and can be adjusted before implementation. AI helps with research and code; each partner checks the evidence and can explain their component.')
D.add_page_break()
h('Stages and completion gates')
for title,text,gate in [
('1 Prove feasibility','You find public rehabilitation disclosures and list missing model inputs. Kevin locates Nyanzaga and finds usable historical imagery for at least two dates. Together, select the area and decide which changes can be interpreted reliably.','Gate: a documented site boundary or clearly labelled study area, usable imagery, and a list separating sourced values from assumptions.'),
('2 Build separate components','You build a model of rehabilitation spending, inflation, timing, and discounted cost. Kevin creates a map and reviewed measurements of visible land change. Agree the shared data format before either component becomes complex.','Gate: each component works independently and has a small demonstration dataset.'),
('3 Connect the prototype','You connect the imagery outputs to the interface and scenario model. Kevin checks spatial units, dates, classifications, and map annotations. Keep derived financial estimates separate from observed measurements.','Gate: a user can inspect an area, change assumptions, and compare scenarios with sources visible.'),
('4 Validate and present','You check calculations against worked examples. Kevin reviews the imagery interpretation and economic assumptions. Together, prepare a short demonstration and a one page explanation of the method and limits.','Gate: reproducible results, documented limitations, and a demonstration both partners can explain.')]:
 D.add_heading(title,2);p(text);p(gate)
h('Fallbacks that keep the project achievable')
bullet('If automatic change detection is unreliable, use manually reviewed areas and retain the source images.')
bullet('If mine specific rehabilitation costs are unavailable, use editable illustrative assumptions. Do not assign group provisions to Nyanzaga without supporting evidence.')
bullet('If timing cannot be estimated from public sources, let users choose scenario dates instead of presenting a forecast.')
p('Satellite images alone cannot establish a rehabilitation liability, prove that rehabilitation is complete, or determine that a company’s provision is incorrect. Operational specialists must validate eligible areas and engineering cost assumptions.')
D.add_page_break()
h('GitHub task backlog')
p('Create one issue per task. Each issue must contain the owner, deliverable, files involved, dependencies, evidence, and completion criteria.')
tasks=[
('01','Agree scope','Both','Approve the case study, user journey, role split, and exclusions.'),
('02','Assess imagery','Kevin','Document location, boundaries, image dates, cloud quality, and data access terms. Depends on 01.'),
('03','Research disclosures','You','Record financial sources and missing cost, timing, and accounting inputs. Depends on 01.'),
('04','Define data contract','Both','Agree field names, units, coordinate system, sources, uncertainty, and missing values. Depends on 02 and 03.'),
('05','Build map demonstration','Kevin','Provide reviewed areas, measurements, and reproducible processing instructions. Depends on 04.'),
('06','Build scenario model','You','Provide calculations, editable assumptions, and worked checks. Depends on 04.'),
('07','Integrate website','You','Connect the map and model; Kevin reviews maps. Depends on 05 and 06.'),
('08','Validate and present','Both','Review outputs, record limits, and prepare the demonstration. Depends on 07.')]
table(['Task','Owner','Deliverable'],[(a+' '+b,c,d) for a,b,c,d in tasks],[1.7,.8,4.3])
h('Checks before calling a task complete')
bullet('Imagery: distinguish vegetation seasonality, agriculture, clouds, and construction from mine related disturbance where evidence allows. Mark uncertain classifications.')
bullet('Model: retain units and currency; distinguish nominal spending from discounted value. Earlier rehabilitation may shift costs rather than reduce them.')
bullet('Integration: verify that changing an input updates the correct output. Every reported measurement or financial assumption has a source or an explicit assumption label.')
bullet('Presentation: explain what is observed, what is modelled, and what needs specialist validation. Do not promise savings based on illustrative scenarios.')
D.add_page_break()
h('Shared repository and AI workflow')
p('Use one shared GitHub repository. Work on separate branches and submit pull requests for the other partner to review. Agree changes to shared interfaces before implementation. Keep large imagery files outside GitHub; commit small samples and reproduction instructions. Keep credentials out of the repository.')
table(['Folder','Contents'],[('app/','Website, map display, and scenario controls'),('model/','Financial calculations and checks'),('imagery/','Satellite processing and map outputs'),('data/sample/','Small demonstration datasets'),('docs/','Sources, assumptions, methodology, and decisions')],[1.6,5.2])
D.add_heading('Keep ChatGPT and Claude aligned',2)
p('Maintain a project brief, a data contract, and a decision log in docs/. Give both assistants the current versions before assigning work. A task handoff should specify its issue, scope, input files, expected output, and completion criteria.')
p('The data contract should include area identifiers, measurement dates, area units, coordinate system, classification method, uncertainty, and source references. Financial inputs should state currency, price base date, cost basis, inflation assumptions, scenario timing, and discount convention. Where area based costs are used, identify separately any fixed costs and obligations the proxy excludes.')
D.add_heading('First demonstration sequence',2)
for t in ['Open Nyanzaga and compare two dated images.','Inspect a reviewed land change area and its uncertainty.','Adjust rehabilitation cost, inflation, and timing assumptions.','Compare the cash flow and discounted cost scenarios.','Open the supporting sources and explain the model’s limits.']:p(t,'List Number')
p('Add AI generated explanations after the map and financial model work. Before choosing hosting, measure the imagery processing requirements; heavy processing can happen offline while the website serves prepared outputs. No repository creation, account setup, or deployment is included in this document task.')
D.add_heading('Starting references',2)
for t in [
'Perseus Mining Nyanzaga project: https://perseusmining.com/nyanzaga/',
'Perseus Mining reports: https://perseusmining.com/reports/',
'Digital Earth Africa datasets: https://docs.digitalearthafrica.org/en/latest/data_specs/index.html',
'Mine rehabilitation monitoring example in Australia: https://knowledge.dea.ga.gov.au/notebooks/Interactive_apps/Mining_rehabilitation/']:
 para=p(t)
 for r in para.runs:r.font.size=Pt(9)
D.core_properties.title='Mining Rehabilitation Research Prototype';D.core_properties.subject='Joint project plan and task split';D.core_properties.author=''
D.save('outputs/Mining_Rehabilitation_Project_Plan.docx')
