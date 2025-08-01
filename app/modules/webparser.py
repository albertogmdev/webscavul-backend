import app.utils.utils as utils

from app.core.webpage import WebPage, MetaTag, Form, Field, Link, ScriptTag, LinkTag
from bs4 import BeautifulSoup
from bs4.element import Tag

def parse_webpage(webpage: WebPage):
    if not webpage.content:
        return {}
    
    soup = BeautifulSoup(webpage.content, 'html.parser')

    parse_links(soup, webpage) 
    parse_metatags(soup, webpage)
    parse_scripttags(soup, webpage)
    parse_linktags(soup, webpage)
    parse_forms(soup, webpage)

def parse_metatags(soup: BeautifulSoup, webpage: WebPage):
    print("INFO: Parsing metas in the webpage")
    for meta in soup.find_all('meta'):
        meta_name = meta.get('name')
        meta_content = meta.get('content')
        meta_http = meta.get('http-equiv')
        meta_charset = meta.get('charset')
        if meta_name and meta_content or meta_http or meta_charset:
            #print('[META]', meta_name, meta_content, meta_http, meta_charset)
            webpage.add_meta_tag(MetaTag(meta_name, meta_content, meta_http, meta_charset, meta))

def parse_forms(soup: BeautifulSoup, webpage: WebPage):
    print("INFO: Parsing forms in the webpage")
    form_index = 1
    for form in soup.find_all('form'):
        form_id = form.get('id')
        form_class = form.get('class')
        if not form_id:
            form_id = f'form:nth-child({form_index})'
        form_method = form.get('method')
        if form_method:
            form_method = form_method.upper()
        form_action = form.get('action')

        formObject = Form(form_id, form_class, form_action, form_method)

        parse_fields(form, formObject)
        form_type = determine_formtype(formObject, form, webpage.url)

        if form_type: 
            formObject.set_form_type(form_type)

        #print('[FORM]', form_id, form_action, form_method, form_type)
        webpage.add_form(formObject)

        form_index += 1

def parse_fields(form: BeautifulSoup, formObject: Form):
    for field in form.find_all(['input', 'select', 'textarea']):
        field_id = field.get('id')
        field_class = field.get('class')
        field_name = field.get('name')
        field_type = field.get('type', 'text')
        if field.name == 'select' or field.name == 'textarea': field_type = field.name
        field_value = field.get('value', '')
        field_placeholder = field.get('placeholder', '')

        #print('[FIELD]', field_id, field_class, field_name, field_type, field_value, field_placeholder)
        formObject.add_field(Field(field_id, field_class, field_name, field_type, field_value, field_placeholder, field))

def parse_links(soup: BeautifulSoup, webpage: WebPage):
    print("INFO: Parsing links in the webpage")
    for link in soup.find_all('a'):
        link_href = link.get('href')
        link_text = link.get_text().strip()
        link_target = link.get('target')
        link_rel = link.get('rel')

        #print('[LINK]', link_href, link_text, link_rel, link_target)
        webpage.add_link(Link(link_href, link_text, link_rel, link_target, link))

def parse_linktags(soup: BeautifulSoup, webpage: WebPage):
    print("INFO: Parsing link tags in the webpage")
    for link in soup.find_all('link'):
        link_href = link.get('href')
        link_rel = link.get('rel')
        link_type = link.get('type')
        link_integrity = link.get('integrity')
        link_crossorigin = link.get('crossorigin')
        link_external = link_href and webpage.domain not in link_href and not link_href.startswith('/')

        #print('[LINKTAG]', link_href, link_rel, link_type, link_integrity, link_crossorigin, link_external)
        webpage.add_link_tag(LinkTag(link_href, link_rel, link_type, link_external, link_integrity, link_crossorigin, link))

def parse_scripttags(soup: BeautifulSoup, webpage: WebPage):
    print("INFO: Parsing scripts in the webpage")
    for script in soup.find_all('script'):
        script_src = script.get('src')
        script_type = script.get('type')
        script_crossorigin = script.get('crossorigin')
        script_integrity = script.get('integrity')
        script_content = script.string
        script_external = script_src and webpage.domain not in script_src and not script_src.startswith('/')

        #print('[SCRIPT]', script_src, script_type, script_crossorigin, script_integrity, script_external)
        webpage.add_script_tag(ScriptTag(script_src, script_type, script_external, script_crossorigin, script_integrity, script_content, script))
        
def determine_formtype(form: Form, form_element: BeautifulSoup, url: str):
    form_type = None
    total_count = form.fields_count["total"]
    url_type = None
    keywords = {
        "login": ["login", "signin", "auth", "access", "identify", "acceso", "acceder", "entrar", "identificacion", "identificar", "autenticar", "autenticacion", "iniciosesion", "iniciarsesion"],
        "signup": ["register", "signup", "createaccount", "newaccount", "accountnew", "join", "registro", "registrar", "crearcuenta", "crearunacuenta", "nuevacuenta", "cuentanueva", "registrarme", "alta", "unirse", "unirme"],
        "search": ["search", "query", "find", "busqueda", "buscar", "buscador"],
        "contact": ["contact", "message", "inquiry", "feedback",  "support", "help", "contacto", "contactar", "ayuda", "soporte", "consulta"],
    }
    types = {
        "login": 0,
        "signup": 0,
        "search": 0,
        "contact": 0
    }

    # Check page url
    paths = url.split("/")
    if paths and len(paths) > 1:
        url_path = " ".join(paths[1:]).lower().replace('-', '').replace('_', '')
        for type, values in keywords.items():
            for keyword in values:
                if keyword in url_path: 
                    url_type = type
                    types[type] += 10
                    break
    
    # Checkt form id, action and classes
    formated_info = form.format_form_info()
    if formated_info and formated_info != "":   
        for type, values in keywords.items():
            for keyword in values:
                if keyword in formated_info:
                    # When there is a form in other URL form
                    if url_type and url_type != type: 
                        types[url_type] -= 10
                        url_type = None
                    types[type] += 10
                    break

    # Check submit input/button
    submit_elements = form_element.find_all(
        lambda tag: (tag.name == 'button' and tag.get('type') == 'submit') or (tag.name == 'input' and tag.get('type') == 'submit')
    )
    submit_info = []
    for element in submit_elements:
        info = ""
        element_name = element.get('name')
        element_text = element.text
        element_value = element.get('value')
        element_id = element.get('id')
        element_class = element.get('class')

        if element_id and element_id != "":
            info += f"{element_id.lower().replace('-', '').replace('_', '')} "
        if element_value and element_value != "":
            info += f"{element_value.lower().replace('-', '').replace('_', '')} "
        if element_text and element_text != "":
            info += f"{element_text.lower().replace('-', '').replace('_', '')} "
        if element_name and element_name != "":
            info += f"{element_name.lower().replace('-', '').replace('_', '')} "
        if element_class and len(element_class) > 0:
            info += f"{" ".join(element_class).lower().replace('-', '').replace('_', '')} "

        if info != "": submit_info.append(info)
    
    for type, values in keywords.items():
        type_found = False
        for keyword in values:
            for info in submit_info:
                if keyword in info: 
                    types[type] += 5
                    type_found = True
                    break
            if type_found:
                break
    
    # Check tag with text
    form_texts = []
    for element in form_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element and element.text and element.text != "":
            formatted_text = utils.remove_accents(element.text.lower().strip().replace(" ", ""))
            form_texts.append(formatted_text)
    for element in form_element.find_all('div'):
        has_child_tags = any(isinstance(child, Tag) for child in element.children)
        has_text = element.text.strip() != ""
        if not has_child_tags and has_text:
            formatted_text = utils.remove_accents(element.text.lower().strip().replace(" ", ""))
            form_texts.append(formatted_text)

    for element in form_texts:
        for type, values in keywords.items():
            for keyword in values:
                if keyword in element: 
                    types[type] += 5
                    break
    for type, values in keywords.items():
        type_found = False
        for keyword in values:
            for text in form_texts:
                if keyword in text: 
                    types[type] += 5
                    type_found = True
                    break
            if type_found:
                break

    # Heuristic for login form
    allowed_login_inputs = ["password", "text", "submit", "email", "checkbox", "button"]
    if total_count <= 5 and total_count >= 2: types["login"] += 2
    else: types["login"] -= 3
    if form.method and form.method != "" and form.method == "POST": types["login"] += 1
    for input, count in form.fields_count.items():
        if input == "password" and count == 1: types["login"] += 3
        elif input == "password"and count != 1: types["login"] -= 5
        if input not in allowed_login_inputs: types["login"] -= 1

    # Heuristic for signup form
    if total_count <= 5 and total_count >= 2: types["signup"] += 2
    if form.method and form.method != "" and form.method == "POST": types["signup"] += 1
    for input, count in form.fields_count.items():
        if input == "password" and count == 1: types["signup"] += 1
        elif input == "password" and count == 2: types["signup"] += 4

    # Heuristic for search form, usually a 2 or 3 inputs, with a text/search input and maybe a submit
    allowed_search_inputs = ["search", "text", "submit"]
    if total_count <= 3: types["search"] += 2
    if form.method and form.method != "" and form.method == "GET": types["search"] += 1
    else: types["search"] -= 3
    for input, count in form.fields_count.items(): 
        if input == "search": types["search"] += 5
        elif input not in allowed_search_inputs: types["search"] -= 1
    
    # Heuristic for contact form
    if form.method and form.method != "" and form.method == "GET": types["contact"] += 1
    if "textarea" in form.fields_count: types["contact"] += 3

    # max_value = -100
    # selected_type = None
    # multiple_types = False
    # for type, value in types.items():
    #     if value > max_value:
    #         max_value = value
    #         selected_type = type
    #         multiple_types = False
    #     if value == max_value and value > 0:
    #         multiple_types = True
    
    max_score = max(types.values())
    likely_types = [t for t, score in types.items() if score == max_score]
    if max_score > 6:
        if len(likely_types) == 1: form_type = likely_types[0]
        elif len(likely_types) > 1: form_type = " / ".join(likely_types)
        else: form_type = "unidentify"
    else:
        form_type = "unidentify"

    return form_type