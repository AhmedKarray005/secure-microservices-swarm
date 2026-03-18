FROM alpine:3.20

RUN addgroup -S monitor && adduser -S -G monitor monitor

COPY monitor.sh /monitor.sh
RUN chmod 755 /monitor.sh

USER monitor

ENTRYPOINT ["/monitor.sh"]
