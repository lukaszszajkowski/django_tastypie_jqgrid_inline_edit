# coding: utf-8

# Copyright 2013 Michał migajek Gajek
# 

 
class JqGridMixin(object):    
    grid = None
    
    def get_context_data(self, **kwargs):
        context = super(JqGridMixin, self).get_context_data(**kwargs)
        context.update({
            'grid_options_js': self.grid.get_grid_final_options_js(self.request.user),            
        })
        return context 