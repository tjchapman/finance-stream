FROM grafana/grafana:10.4.14-ubuntu

# Disable Login form or not
ENV GF_AUTH_DISABLE_LOGIN_FORM "true"
# Allow anonymous authentication or not
ENV GF_AUTH_ANONYMOUS_ENABLED "true"
# Role of anonymous user
ENV GF_AUTH_ANONYMOUS_ORG_ROLE "Admin"

# Add provisioning
COPY ./provisioning /etc/grafana/provisioning
# Add configuration file
COPY ./grafana.ini /etc/grafana/grafana.ini

RUN grafana cli plugins install hadesarchitect-cassandra-datasource

