from pyhtmlgui import PyHtmlView


class Settings_trackstop(PyHtmlView):
    TEMPLATE_STR = '''


        <div class="row h-3of12">
        
        
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.togglefilter, "blockads")'>
                <div class="row tile-body {% if pyview.subject.userapi._get_bool_value("blockads") %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> Ads </h3>
                </div>
            </div>
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.togglefilter, "social")'>
                <div class="row tile-body {% if pyview.subject.userapi._get_bool_value("social") %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> social </h3>
                </div>
            </div>    
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.togglefilter, "kids")'>
                <div class="row tile-body {% if pyview.subject.userapi._get_bool_value("kids") %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> Kids </h3>
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
        super(Settings_trackstop, self).__init__(subject, parent)
        self.on_back = on_back

    def state_change(self, *args, **kwargs):
        self.update()

    def togglefilter(self, filtername):
        if  self.obj.userapi._get_bool_value(filtername) is True:
            self.obj.userapi._set_bool_value(filtername, False)
        else:
            self.obj.userapi._set_bool_value(filtername, True)
        self.update()