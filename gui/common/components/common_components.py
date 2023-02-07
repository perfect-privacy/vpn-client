from pyhtmlgui import PyHtmlView


class SelectComponent(PyHtmlView):
    TEMPLATE_STR = '''
    <label for="select_{{ pyview.uid }}"> {{pyview.label}} </label>
    <div id="select_{{ pyview.uid }}" class="nice-select" onclick="if(!this.classList.contains('open')){this.classList.toggle('open');this.children[0].focus();}">
        <input style="position:fixed;left:-9999px;" type="checkbox" onfocusout="setTimeout(function(){ document.getElementById('select_{{ pyview.uid }}').classList.remove('open') }, 200);"></input>
        <div class="current">{{pyview.get_current_valuestr() }}</div>
        <ul class="list">
            {% for option in pyview.options %}
                <li onclick='pyview.set_value("{{option.0}}")' class="option {% if pyview.subject.get() == option.0 %}selected{%endif%}"> {{option.1}} </li>
            {% endfor %}
        </ul>
    </div>        
        
    '''
    def __init__(self, subject, parent, options, label = ""):
        super(SelectComponent, self).__init__(subject, parent)
        self.options = options
        self.label = label
        self.shown = False

    def get_current_valuestr(self):
        for option in self.options:
            if option[0] == self.subject.get():
                return option[1]

    def set_value(self, value ):
        print("set value", value)
        if type(self.options[0][0]) == int:
            value = int(value)
        self.subject.set(value)

class SelectComponentWithSelect(PyHtmlView):
    TEMPLATE_STR = '''
        <label for="select_{{ pyview.uid }}"> {{pyview.label}} </label>
        <select id="select_{{ pyview.uid }}" class="form-control"  onchange='pyview.set_value($("#select_{{ pyview.uid }}").val())'>
            {% for option in pyview.options %}
                <option value="{{option.0}}"   {% if pyview.subject.get() == option.0 %}selected{%endif%} > {{option.1}} </option>
            {% endfor %}
        </select>
    '''
    def __init__(self, subject, parent, options, label = ""):
        super(SelectComponentWithSelect, self).__init__(subject, parent)
        self.options = options
        self.label = label

    def set_value(self, value ):
        if type(self.options[0][0]) == int:
            value = int(value)
        self.subject.set(value)


class CheckboxComponent(PyHtmlView):
    TEMPLATE_STR = '''
        <input 
            onchange='pyview.subject.set($("#checkbox_{{ pyview.uid }}").prop("checked") === true)'  
            class="form-check-input" type="checkbox" value="" id="checkbox_{{ pyview.uid }}" 
            {% if pyview.subject.get() %} checked {% endif %}
        >
        <label class="form-check-label" for="checkbox_{{ pyview.uid }}">
           {{pyview.label}}
        </label>
    '''
    def __init__(self, subject, parent, label = ""):
        super(CheckboxComponent, self).__init__(subject, parent)
        self.label = label

class TextinputComponent(PyHtmlView):
    TEMPLATE_STR = '''
        <input  onchange='$("#textfield_{{ pyview.uid }}").val()' 
            class="form-check-input" type="text" value="{{pyview.subject.get()}}" id="textfield_{{ pyview.uid }}"  
        >
        <label class="form-check-label" for="textfield_{{ pyview.uid }}">
           {{pyview.label}}
        </label>
    '''
    def __init__(self, subject, parent, label = ""):
        super(TextinputComponent, self).__init__(subject, parent)
        self.label = label
