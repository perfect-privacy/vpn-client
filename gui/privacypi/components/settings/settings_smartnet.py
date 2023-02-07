from pyhtmlgui import PyHtmlView


class Settings_smartnet(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-3of12 p-1o6">            


            <div class="col-4 tile" onclick = 'pyhtmlgui.call(pyview.subject.settings.smartnet.enabled.set, true )'>
                <div class="row tile-body {% if pyview.subject.settings.smartnet.enabled.get() %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> ON </h3>
                </div>
            </div>
          
            <div class="col-4 tile" onclick = 'pyhtmlgui.call(pyview.subject.settings.smartnet.enabled.set, false )'>
                <div class="row tile-body {% if not pyview.subject.settings.smartnet.enabled.get() %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> Off </h3>
                </div>
            </div>
            
        </div>

        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 bottom_tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
                <div class="bottom_tile-body">
                     <h3 class="verticalcenter"><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
                </div>
            </div>

            <div class="col-4">
            </div>

            <div class="col-4">
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        super(Settings_smartnet, self).__init__(subject, parent)
        self.on_back = on_back
