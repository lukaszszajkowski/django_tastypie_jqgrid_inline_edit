// wrapper of jqGrid which provides helping routines for handling custom options
// this library is part of django-tastypie-jqgrid
// copyright Michal Gajek  	
(function( $ ){	

    var methods = {
        // extends grid options, appending event handlers
        _extendOptions: function(options)
        {                            
                options['serializeGridData']  =  function (postData) 
                {
                    // prepare data for Tatsypie format
                    var pdat = $.extend({}, postData);
                                
                    // sorting / ordering                    
                    if (typeof pdat.sidx != 'undefined' && pdat.sidx != '')
                    {
	                    pdat.order_by = pdat.sidx.replace('.', '__');
	                    if (pdat.sord !== 'undefined')
	                                        if (pdat.sord.toLowerCase() == 'desc')
	                                        pdat.order_by = '-' + pdat.order_by;
                    }
                        
                    // filtering
                    if (pdat.filters)
                    {
                            var filters = jQuery.parseJSON(pdat.filters);
                            var ops = {                            			
                            			'eq': 'iexact',
                            			'lt': 'lt',
                            			'le': 'lte',
                            			'gt': 'gt',
                            			'ge': 'gte',
                            			'bw': 'istartswith',
                            			'in': 'in',
                            			'ew': 'iendswith',
                            			'cn': 'icontains',
                            			'dt': false, // special value used by date fields. don't append anything to search condition. 
                            		}
                            $.each(filters.rules, function(idx, rule){
                            		var op = (rule['op'] in ops) ? ops[rule['op']] : 'icontains';
                            		var fieldname = rule['field'];
                            		if (op !== false)
                            			fieldname += '__' + op;
                                    pdat[fieldname] = rule['data'];
                            });
                    }
                    delete pdat.filters;
                    delete pdat.sord;
                            delete pdat.sidx;
                            
                    return pdat;
                }
            return options;
        },

        // return mGrid custom data passed to jqGrid function
        get_custom_data: function(){
                return $(this).jqGrid('getGridParam', 'mGrid');
        },
        
        // initialize grid
        _init : function(options) {
                        var $elem = $(this);
                        options = $elem.mGrid2('_extendOptions', options);                      
                        $elem.jqGrid(options);
                        if (options.mGrid.filter_toolbar)
                        {                        	
                        	$elem.jqGrid('filterToolbar',options.mGrid.filter_toolbar);
                    	}                    	


						$elem.mGrid2('_init_editing');
						$elem.mGrid2('_init_inline_editing', options);
                        //if (options.pager && options.mGrid.pager_options)
                        // init it anyway, as it might be triggered manually
                		$elem.mGrid2('_init_form_editing', options);
                		
                		$elem.mGrid2('_init_custom_pager_buttons')

        },
        
        // initialize common editing options
        _init_editing: function(options)
        {
        	// url need to be provided separately for inline editing and for form editing. see _init_form_editing 
        	$.extend($.jgrid.edit, {
		      ajaxEditOptions: { contentType: "application/json" },
		      mtype: 'PATCH',
		      serializeEditData: function(data) {
		        delete data.oper;
		        if (data.id == '_empty') // who the f*** did invented forcing _empty for an uneditable column?!?!
		        	delete data.id;  
		        return JSON.stringify(data);
		      }		     
		    });
		    $.extend($.jgrid.del, {
		      mtype: 'DELETE',
		      serializeDelData: function() {
		        return "";
		      }
		    });
        }, 
        // initialize form editing with appropriate communication settings 
        _init_form_editing: function(options)
        {
        	// these edit options are initialized once only, as mGrid2 module is loaded.
			$(this).jqGrid('navGrid', options.pager, options.mGrid.pager_options, $.mgrid._editOptions, $.mgrid._addOptions, $.mgrid._delOptions);
        },
        // initialize inline editing
        _init_inline_editing: function(options)
        {
        	if (!options.mGrid || !options.mGrid.automatic_inline_editing)
        		return options;
        	var _lastSelection;
        	$(this).jqGrid('setGridParam', {        		
        		onSelectRow :function (id) {
        				//var $this = $(this),
        			//_lastSelection =  get_custom_data;
		               if (id && id !== _lastSelection) {
		                   var $grid = $(this);
		                   $grid.restoreRow(_lastSelection);
		                   $grid.editRow(id, {
		                   		keys: true,
		                   		url: $grid.jqGrid('getCell',id,'resource_uri')
		                   		});
		                   _lastSelection = id;
		               }
           		},
           		serializeRowData: function (postdata)
           		{
           			return JSON.stringify(postdata);
           		}
       		});
           	
           	return options;

        },
        
        // initialize custom buttons with data-mgrid* attributes
        _init_custom_pager_buttons: function()
        {
        	var $this = $(this),
        		$buttons = $('a[data-mgrid-selector=#'+$this.attr('id')+']');
        		
        		$buttons.click(function(e){
        			e.preventDefault();
        			var $this = $(this),
        				oper = $this.attr('data-mgrid-oper'),
        				$grid = $($this.attr('data-mgrid-selector'));
        				
        				if (oper === 'custom')
        				{
        					var 
        						_pk = $grid.mGrid2('get_selected_row_id'),
        						goto_url = $this.data('mgrid-gotourl').replace('{pk}', _pk);
        					location.href = goto_url;
        				} else if (oper === 'add')
        					$grid.jqGrid("editGridRow","new", $.mgrid._addOptions);
    					else if (oper === 'edit' || oper === 'delete')
    					{
    						var selrow = $grid.mGrid2('get_selected_row_id');
    						if (!selrow)
    						{
    							$.jgrid.viewModal("#alertmod",{gbox:"#gbox_"+$.jgrid.jqID($grid.attr('id')),jqm:true});
								$("#jqg_alrt").focus();
    						} else {
    							if (oper === 'edit')
    								$grid.jqGrid("editGridRow", selrow, $.mgrid._editOptions);
								else if (oper === 'delete')
									$grid.jqGrid("delGridRow", selrow, $.mgrid._delOptions);
							}
    					} else if (oper === 'refresh')
    					{
    						$grid.trigger("reloadGrid")
    					}    					
        			return false;
        		})
        	
        },        
        _init_grid_tabs: function()
        {
                // handle "All" tab click
                $('a[data-grid-reset-filters]').click(function(e){
                                e.preventDefault();
                                var $this = $(this),
                                        $grid = $($this.attr('data-grid-name')).mGrid2('reset_default_url');
                                $this.parents('ul').find('li').removeClass('active');
                                $this.parent().addClass('active');
                                return false;
                        });
                        // handle "<filter name>" tab click
                        $('a[data-set-grid-filter]').click(function(e){
                                e.preventDefault();
                                var $this = $(this);
                                var $grid = $($this.attr('data-grid-name'));
                                if ($grid.mGrid2('set_filter_name', $this.attr('data-set-grid-filter')))
                                {
                                        $this.parents('ul').find('li').removeClass('active');
                                        $this.parent().addClass('active');
                                }
                                return false;
                        });
        },
        
        // set grid's url to default again
        reset_default_url : function() {
                var $this = $(this);
                $this.mGrid2('set_grid_url', $this.mGrid2('get_custom_data').default_url)
                        .jqGrid('setGridParam', {'mGrid': {'current_filter': null}});                   
        },
        
        get_url_for_filter: function(filter_name){
                if (!filter_name)
                         return $(this).mGrid2('get_custom_data').default_url
                 else
                 {
                        var filters = $(this).mGrid2('get_custom_data').filters;
                        for (var i = 0; i < filters.length; i++)
                                if (filters[i].name == filter_name)
                                        return filters[i].url           
                                return false;
                        }
        },
        
        get_current_url: function()
        {
                var $this = $(this),
                        curr_filter = $this.mGrid2('get_custom_data').current_filter;
                        return $(this).mGrid2('get_url_for_filter', curr_filter);
        },
        
        set_grid_url: function(url)
        {
                $(this).jqGrid('setGridParam', {'url': url}).trigger('reloadGrid');
                return $(this);
        },
        
        // set filter URL by name (if provided in custom grid options, generated 
        // according to NBResource filtering options & JqGridMixin filtering data)
        set_filter_name : function(filter_name) {
                var $this = $(this),
                        url_to_set = $this.mGrid2('get_url_for_filter', filter_name);
                        
                if (url_to_set)         
                                $this.mGrid2('set_grid_url', url_to_set)
                                        .jqGrid('setGridParam', {'mGrid': {'current_filter': filter_name}});                                    
                                        
                        return url_to_set;
        },
        
        // set filtering attributes
        // array of filter object, each having name: value: and optional match: type
        set_filters: function(filters_array){
                var $this = $(this),
                        // append to current URL as we might want to search on already filtered results
                        url = $this.mGrid2('get_current_url');
                
                $.each(filters_array,function(idx, filter){
                        if (idx == 0 && url.indexOf('?') == -1) // if this is the first param
                                                                                                        // and no query appended so far, add it
                                url += '?';
                                else
                                        url += '&';
                                name = filter.name + '__' + (filter.match || 'icontains');
                                url += name + '=' + encodeURIComponent(filter.value);
                                
                });
                
                $this.mGrid2('set_grid_url', url);
                        
        },
        
        // returns selected row id (_pk)
        get_selected_row_id: function()
        {        	
        	var
    			selRowId = $(this).jqGrid ('getGridParam', 'selrow'),
    			celValue = $(this).jqGrid ('getCell', selRowId, '_pk');
    			return celValue;
        }
    };

    $.fn.mGrid2 = function(methodOrOptions) {
        if ( methods[methodOrOptions] ) {
            return methods[ methodOrOptions ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof methodOrOptions === 'object' || ! methodOrOptions ) {                           
            return methods._init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.mGrid2' );
        }    
    };

	$.mgrid = {};
	$.mgrid._delOptions = {
		    	onclickSubmit: function(params, postdata) {
		    		params.url = $(this).jqGrid('getRowData', postdata).resource_uri;
	  			} 
	};
	$.mgrid._addOptions = {
		mtype: "POST", 
		
	};
	$.mgrid._editOptions = {
		mtype: "PATCH",
		onclickSubmit: function(params, postdata) {
			var row_id = postdata[$(this).attr('id')+'_id'];
			params.url = $(this).jqGrid('getRowData', row_id).resource_uri;
		},
		beforeShowForm: function(form){
			$('[data-mgrid-clear-onshow]', form).removeAttr('value').removeClass('FormElement');
			setTimeout(function(){$('[data-mgrid-formelement]', form).removeClass('FormElement');}, 200);
		},
		viewPagerButtons: false
	}



	// CSRF token is needed
	function loadBeforeSend(xhr, settings)
	{
	        function getCookie(name) {
	             var cookieValue = null;
	             if (document.cookie && document.cookie != '') {
	                 var cookies = document.cookie.split(';');
	                 for (var i = 0; i < cookies.length; i++) {
	                     var cookie = jQuery.trim(cookies[i]);
	                     // Does this cookie string begin with the name we want?
	                 if (cookie.substring(0, name.length + 1) == (name + '=')) {
	                     cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                     break;
	                 }
	             }
	         }
	         return cookieValue;
	         }
	         if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
	             // Only send the token to relative URLs i.e. locally.
	             xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
	             xhr.setRequestHeader("HTTP_X_CSRFTOKEN", getCookie('csrftoken'));
	         }
	}
	$(function(){
        $.ajaxSetup({
                beforeSend: loadBeforeSend
        })
	});
})( jQuery );