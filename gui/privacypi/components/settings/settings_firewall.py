from pyhtmlgui import PyHtmlView


class Settings_firewall(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-1of3">
            <div class="col-4">
            on
            </div>

            <div class="col-4">
            info
            </div>

            <div class="col-4">
            off
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
        super(Settings_firewall, self).__init__(subject, parent)
        self.on_back = on_back
