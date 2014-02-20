from django.db import models
# Create your models here.

import logging
l = logging.getLogger('django.db.backends')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())


class Pensioner(models.Model):
    reference = models.CharField(max_length=7, blank=False, null=False, primary_key=True)
    title = models.CharField(max_length=10)
    forename = models.CharField(max_length=32)
    surname = models.CharField(max_length=20)

    def __unicode__(self):
        return '%s %s' % (self.forename, self.surname)
        #return u'"%s" by %s' % (self.title, unicode(self.author))

    def __str__(self):
        return '%s %s' % (self.forename, self.surname)

    class Meta:
        db_table = 'pensioner'
        managed = True


