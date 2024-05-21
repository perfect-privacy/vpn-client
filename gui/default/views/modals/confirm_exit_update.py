from .modal import Modal

class ConfirmExitUpdateModalView(Modal):
    """
    :type subject: core.Core
    :type parent: gui.default.components.dashboard.DashboardView
    """
    TEMPLATE_STR = '''   
        {% if pyview.display %}
            <div id="confirmLogoutModal" class="modal">
                <div class="modal-content" style="margin: 15% auto 5% auto;height: 50%;text-align:center">
                    <h2 style="padding: 2em;"> {{_("Update VPN client now?")}}</h2>
                    {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                        <h3 style="padding-bottom: 2em;"> {{_("This will <b>disconnect</b> all existing VPN Tunnels!")}} </h3>
                    {% endif %}
                    <button onclick="pyview.exit_app()">{{_("Yes")}}</button>
                    <button onclick="pyview.hide()">{{_("No")}}</button>
                </div>
            </div>
        {% endif %}
    '''

    def exit_app(self):
        self.subject.on_frontend_exit_by_user(for_update=True)
        self.eval_javascript("pyhtmlapp.exit_app_for_update()", skip_results=True)
        self.hide()
