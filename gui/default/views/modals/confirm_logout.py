from .modal import Modal

class ConfirmLogoutModalView(Modal):
    """
    :type subject: core.Core
    :type parent: gui.default.components.dashboard.DashboardView
    """
    TEMPLATE_STR = '''   
        {% if pyview.display %}
            <div id="confirmLogoutModal" class="modal">
                <div class="modal-content" style="margin: 15% auto 5% auto;height: 50%;text-align:center">
                    <h2 style="padding: 2em;"> {{_("Are you sure you want to logout?")}}</h2>
                    {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                        <h3> {{_("This will <b>disconnect</b> any existing VPN Tunnels!")}} </h3>
                    {% endif %}
                    <button onclick="pyview.logout()">{{_("Yes")}}</button>
                    <button onclick="pyview.hide()">{{_("No")}}</button>
                </div>
            </div>
        {% endif %}
    '''
    def logout(self):
        self.hide()
        self.subject.settings.account.logout()
        self.subject.userapi.request_update()
        self.subject.session.disconnect()
