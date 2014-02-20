__author__ = 'Lukasz'
from tastypie_jqgrid.grids import JqGrid
from .resources import PensionerResource

# zero-configuration grid. Works fine for read only access.
class PensionerGrid(JqGrid):
    class GridOptions:
        grid_resource = PensionerResource

# customized, full-featured grid
class CustomPensionerGrid(PensionerGrid):
    class GridOptions:
        filtering_toolbar = True
        columns_editable_by_default = True
        pager_selector = '#gridpager'
        pager_options = {'search': True} # hidden search button
        scroll = False  # disable scrolling, we have pagination

        #default_sort = '-forename'

    def get_grid_options(self, user):
        return {
                'viewrecords': True
        }

class InlineEditPensionerGrid(PensionerGrid):
    class GridOptions:
        automatic_inline_editing = True
        columns_editable_by_default = True
