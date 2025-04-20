from djoser.email import ActivationEmail


class CustomActivationEmail(ActivationEmail):
    template_name = 'djoser/email/activation.html'

    def get_context_data(self):
        # Call the base implementation first to get a context dictionary
        context = super().get_context_data()

        # Ensure correct values are set for protocol and domain
        request = self.context.get('request')
        if request:
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()  # This will provide the correct domain, without protocol
        else:
            protocol = 'http'  # Default fallback
            domain = '127.0.0.1:8000'  # Replace with your actual domain for production

        # Construct the activation URL properly
        uid = context.get('uid')
        token = context.get('token')
        activation_url = f"{protocol}://{domain}/activate/{uid}/{token}/"

        context['activation_url'] = activation_url

        return context
