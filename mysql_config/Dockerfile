FROM mysql:8

# Copier la config dans le dossier approprié
COPY my.cnf /etc/mysql/conf.d/my.cnf

# Fixer les permissions
RUN chmod 644 /etc/mysql/conf.d/my.cnf