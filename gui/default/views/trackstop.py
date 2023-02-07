from pyhtmlgui import PyHtmlView
from gui.common.components import CheckboxComponent

class TrackstopView(PyHtmlView):
    TEMPLATE_STR = '''
        {% if pyview.subject.userapi.credentials_valid.get() != True %}
            <div class="not_logged_in">
                Login to change your TrackStop settings.
            </div>
        {% endif %}
    
        <div class="inner">
            <h1>TrackStop</h1>
            <p>
                The TrackStop feature allows you to block unwanted domains directly on VPN level.  You can choose what kind of domains you want to block by activating one or more of the filters.
                <br>
                Note: Understand what a filter does block before activating and testing it. It might take up to 3 minutes for any changes.
            </p>
            
            <div class="boxes">
                
                <section>
                    <h3>
                        Ads / Analytics
                        <div class="input">  {{ pyview.block_ads.render() }} </div>
                    </h3> 
                    <div>Protect your privacy and block over 30,000 tracking and advertisement domains with this filter</div>
                </section>
                
                <section>
                    <h3>
                        Fraud / Malware
                        <div class="input"> {{ pyview.block_fraud.render() }} </div>
                    </h3> 
                    <div>Activate this filter to block over 65,000 known malware and phishing domains.</div>
                </section>
                
                <section>
                    <h3>
                        Google Services
                        <div class="input"> {{ pyview.block_google.render() }} </div>
                    </h3> 
                    <div> Warning: This blocks all Google domains, including YouTube, ReCaptcha and many other services from Google used on many websites!  </div>
                </section>
                
                <section>
                    <h3>
                        Facebook
                        <div class="input"> {{ pyview.block_facebook.render() }}</div>
                    </h3> 
                    <div>Activate this filter and block all Facebook domains.</div>
                </section>
                
                <section>
                    <h3>
                        All social media
                        <div class="input"> {{ pyview.block_social.render() }} </div>
                    </h3> 
                    <div>Block all major social media sites. including Facebook, Twitter, Tumblr, Instagram, Google+, Pinterest, MySpace and LinkedIn.</div>
                </section>
    
                <section>
                    <h3>
                        Fakenews
                        <div class="input"> {{ pyview.block_fakenews.render() }} </div>
                    </h3> 
                    <div> Block domains known to publish fake news using a publicly available filter list hosted on GitHub that anyone can contribute to.</div>
                </section>
                            
                <section>
                    <h3>
                        Adult content
                        <div class="input"> {{ pyview.block_kids.render() }} </div>
                    </h3> 
                    <div>Block a large number of websites that are inappropriate for children, such as pornographic content and gambling. This filter also includes the block lists for tracking and advertisement as well as fraud, so those filters do not need to be activated separately.</div>
                </section>
            </div>						
        </div>						
    '''

    def __init__(self, subject, parent):
        '''
        :type subject : core.Core
        :param parent: gui.modern.components.mainview.MainView
        '''
        self._on_subject_updated = None
        super(TrackstopView, self).__init__(subject, parent)
        self.block_kids = CheckboxComponent(subject.userapi.trackstop.block_kids, self, label="")
        self.block_ads = CheckboxComponent(subject.userapi.trackstop.block_ads, self, label="")
        self.block_facebook = CheckboxComponent(subject.userapi.trackstop.block_facebook, self, label="")
        self.block_fakenews = CheckboxComponent(subject.userapi.trackstop.block_fakenews, self, label="")
        self.block_fraud = CheckboxComponent(subject.userapi.trackstop.block_fraud, self, label="")
        self.block_google = CheckboxComponent(subject.userapi.trackstop.block_google, self, label="")
        self.block_social = CheckboxComponent(subject.userapi.trackstop.block_social, self, label="")
