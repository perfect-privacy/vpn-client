from .modal import Modal

class ConfirmExitModalView(Modal):
    """
    :type subject: core.Core
    :type parent: gui.default.components.dashboard.DashboardView
    """
    TEMPLATE_STR = '''   
        {% if pyview.display %}
            <div id="confirmLogoutModal" class="modal">
                <div class="modal-content" style="margin: 15% auto 5% auto;height: 50%;text-align:center">
                    <h2 style="padding: 2em;"> Are you sure you want to Exit?</h2>
                    {% if pyview.subject.settings.startup.enable_background_mode.get() == False %}
                        {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                            <h3> This will <b>disconnect</b> all existing VPN Tunnels! </h3>
                        {% endif %}
                    {% else %}
                         {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                            <h3> Background mode enabled, your VPN connections will stay active!</h3>
                        {% else %}
                            {% if pyview.subject.settings.leakprotection.leakprotection_scope.get() == "program" %}
                                <h3> Background mode enabled, Leak Protection will stay active!</h3>
                            {% endif %}
                        {% endif %}
                    {% endif %}
                    <button onclick="pyview.exit_app()">Yes</button>
                    <button onclick="pyview.hide()">No</button>
                </div>
            </div>
        {% endif %}
    '''

    def exit_app(self):
        self.subject.on_frontend_exit_by_user()
        self.eval_javascript("pyhtmlapp.exit_app()", skip_results=True)
        self.hide()
