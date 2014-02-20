from tastypie.paginator import Paginator
from tastypie.exceptions import BadRequest


class JqGridPaginator(Paginator):    
    def get_limit(self):
        limit = self.request_data.get('rows', self.limit)
        if limit is None:            
            return super(JqGridPaginator, self).get_limit()
        
        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer." % limit)

        if limit < 0:
            raise BadRequest("Invalid limit '%s' provided. Please provide a positive integer >= 0." % limit)

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            return self.max_limit
        return limit
    
    def get_offset(self):        
        if 'page' in self.request_data:
            page = self.request_data.get('page', 1)
            
            try:
                page = int(page)
            except ValueError:
                raise BadRequest("Invalid page '%s' provided. Please provide an integer." % page)
            
            if page < 0:
                raise BadRequest("Invalid page '%s' provided. Please provide a positive integer >= 0." % page)
            
            offset = self.get_limit() * (page - 1)
            
            return offset
        
        return super(JqGridPaginator, self).get_offset()