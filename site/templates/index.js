// Helper function: displays a course in the detail view, no matter how it was clicked
function display(course_id) {
    /* highlight the course if it's in the search results */
    if ($("#result_num_"+course_id).attr('class') !=('course_shown')) {
        $(".course_shown").addClass("course").removeClass("course_shown");//switchClass("course_shown","course");
        $("#result_num_"+course_id).addClass("course_shown").removeClass("course");//switchClass('course','course_shown');
    }
    
    /* show the info */
    if ($("#detail_num_"+course_id).attr('class') != "detail_shown") {
        $(".detail_shown").addClass("detail").removeClass("detail_shown");//switchClass("detail_shown", "detail");                        
        var detail_id = "#detail_num_"+course_id;
        $(detail_id).addClass("detail_shown").removeClass("detail");//switchClass("detail", "detail_shown");
    }
}

// Helper function: handles the post request to get a specific semester of a course.
// params[1] is the course id, params[2] is the term number
function load_semester(params) {
    var detail_id = "#detail_num_"+params[1];
    /* Hide / show selected semester */
    if ($(detail_id+">.detail_sem_"+params[2]).length == 0) {
        $.post("/semester/", $(detail_id+">.semester_menu>.term_selector").serialize(), function( data ) {
            $(detail_id).append(data);
            $(detail_id+">.semester_shown").addClass("semester").removeClass("semester_shown"); //switchClass("semester_shown", "semester");
            $(detail_id+">.detail_sem_"+params[2]).addClass("semester_shown").removeClass("semester"); //switchClass("semester", "semester_shown");
            $(detail_id+">.semester_menu>.reviews_form>input[type=submit]").attr("value", "See Reviews");
        });
    }
    else {
        $(detail_id+">.semester_shown").addClass("semester").removeClass("semester_shown"); //.switchClass("semester_shown", "semester");
        $(detail_id+">.detail_sem_"+params[2]).addClass("semester_shown").removeClass("semester"); //.switchClass("semester", "semester_shown");
        $(detail_id+">.semester_menu>.reviews_form>input[type=submit]").attr("value", "See Reviews");
    }
    /* Enable / disable course history selection buttons */ 
 //   $(detail_id+">.semester_menu>button").removeAttr("disabled");
 //   $(detail_id+">.semester_menu>.semester_"+params[1]+"_"+params[2]).attr("disabled", "disabled");
}

function load_reviews(course_id) {
    var detail_id = "#detail_num_"+course_id;
    if ($(detail_id+">.detail_reviews").hasClass("semester_shown")) {
       var semester_id = $(detail_id+">.semester_menu>.term_selector>select>option:selected").attr("value");
       $(detail_id+">.semester_shown").addClass("semester").removeClass("semester_shown"); //.switchClass("semester_shown", "semester");
       $(detail_id+">.detail_sem_"+semester_id).addClass("semester_shown").removeClass("semester"); //.switchClass("semester", "semester_shown");
       $(detail_id+">.semester_menu>.reviews_form>input[type=submit]").attr("value", "See Reviews");
    }
    else {
	
    /* Hide / show selected semester */
    if ($(detail_id+">.detail_reviews").length == 0) {
        $.post("/reviews/", $(detail_id+">.semester_menu>.reviews_form").serialize(), function( data ) {
            $(detail_id).append(data);
            $(detail_id+">.semester_shown").addClass("semester").removeClass("semester_shown"); //.switchClass("semester_shown", "semester");
            $(detail_id+">.detail_reviews").addClass("semester_shown").removeClass("semester"); //.switchClass("semester", "semester_shown");
            plot_review_data();
        });
    }
    else {
        $(detail_id+">.semester_shown").addClass("semester").removeClass("semester_shown"); //.switchClass("semester_shown", "semester");
        $(detail_id+">.detail_reviews").addClass("semester_shown").removeClass("semester"); //.switchClass("semester", "semester_shown");
        plot_review_data();
    }
    $(detail_id+">.semester_menu>.reviews_form>input[type=submit]").attr("value", "See Course Data");
    }
}

/* function to make the plots of the numerical review data */
function plot_review_data() {
    var data = [
                {label:"Overall", data:[]}, 
                {label:"Lectures", data:[]}
               ];
    var xmapping = [];
    
    /* iterate through all the past semesters of ratings */
    var xval = 0;
    var categories = {"overall_mean": 0, "lectures_mean":1};
    $(".detail_reviews.semester_shown>.detail_ratings_numbers").children().each(function() {
        /* iterate through all the ratings for that semester */
        xmapping.push([ xval, $(this).children().first().text()]);
        $(this).children().each(function() {
            var itemarray = $(this).text().split(":");
            if (itemarray[0] in categories) {
                data[categories[itemarray[0]]]["data"].push([xval, itemarray[1]]);
            }
        });
        xval = xval - 1;
    });
    
    var options = {
                    series: {
                             lines: {show:true}
                            },
                     xaxis: {ticks: xmapping}
                   };
    $.plot($(".detail_shown").find(".detail_ratings_plot"), data, options);
}

/* function to make the spinner */
function make_spinner() {
        var opts = {
        lines: 9, // The number of lines to draw
        length: 5, // The length of each line
        width: 4, // The line thickness
        radius: 6, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        direction: 1, // 1: clockwise, -1: counterclockwise
        color: '#ff4900', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 80, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: '260px' // Left position relative to parent in px
    };
    var target = document.getElementById('omnibar_form');
    var spinner = new Spinner(opts).spin(target);
    return spinner;
}

var spinner_on = false;

$(document).ready(function() {

    /* Enable showing cart courses */
    $(".coursecart").click(function(ev){
        if ($(ev.target).attr("type") == "submit") return;
        var course_id = this.id.split('_')[2];
        $("#right_scrollbar_wrap").css("background-color","rgba(0,0,0,0.9)");
        display(course_id);
    });
    
    /* set the behavior of the "load semester button" */
    $(".semester_menu>.term_selector>.term_dropdown").change(function() {
        var params = $(this).find("option:selected").attr('class').split('_');
        load_semester(params);
    });
    
    /* Load reviews */
    $(".semester_menu>.reviews_form").submit(function(e) {
        e.preventDefault();
        var course_id = $(this).find("input[name=course_id]").attr('value');
        load_reviews(course_id);
    });

    /*set behavior of remove from cart button. Also under search results */
    $(".removecourse_form").submit(function(e) {
        e.preventDefault();
        var course_id = $(this).parent().attr('id').split('_')[2];
        /* send post request to save that the user has removed the course from his/her cart */
        var posting = $.post("/course/remove/", $(this).serialize());
        /* remove the course from the cart list and remove any hidden info about the course */
        $("#cart_num_"+course_id).remove();
        $("#save_"+course_id+">input[type=submit]").removeAttr("disabled");
    });
                        
    /* Show and hide the advanced search dialog */
    $("#show_advanced").click(function(){
        $("#advanced_search_wrapper").fadeIn();
        $("#advanced_search").fadeIn(function() {
            $("#advanced_search_wrapper").click(function(ev) {
                if (ev.target != this) return;
                $("#advanced_search_wrapper").fadeOut();
                $("#advanced_search").fadeOut();
                $("#advanced_search_wrapper").unbind('click');
            });  
        });
    });
    
    $("#hide_advanced").click(function(){
        $("#advanced_search_wrapper").fadeOut();
		$("#advanced_search").fadeOut();
    });
    
    /* Show and hide the analytics */
     $("#show_analytics").click(function(){
        $("#advanced_search_wrapper").fadeIn();
        $("#analytics").fadeIn(function(){
            $("#advanced_search_wrapper").click(function(ev) {
                if (ev.target != this) return;
                $("#advanced_search_wrapper").fadeOut();
                $("#analytics").fadeOut();
                $("#advanced_search_wrapper").unbind('click');
            });  
        });
    });
    
    $("#hide_analytics").click(function(){
        $("#advanced_search_wrapper").fadeOut();
        $("#analytics").fadeOut();
    });
    
    /* Set up the advanced search form */
    /*$( "#advanced_num_slider" ).slider({
      range: true,
      min: 100,
      max: 600,
      values: [ 100, 600 ],
      slide: function( event, ui ) {
        $( "#advanced_num_range" ).val(ui.values[ 0 ] + "-" + ui.values[ 1 ] );
      }
    });
    $( "#advanced_num_range" ).val($( "#advanced_num_slider" ).slider( "values", 0 ) +
      "-" + $( "#advanced_num_slider" ).slider( "values", 1 ) );*/
    
    /* 'Submit' the advanced search form */
    $("#advanced_form").submit(function(event) {
        event.preventDefault();
        var boxes;
        var input = $("#advanced_subject").val();
        if ($("#advanced_course_number").val().trim().length != 0) {
            input += " " + $("#advanced_course_number").val();
        }
        var min = 999;
        var max = 0;
        boxes = $("input[name=level]:checked");
        boxes.each(function(){
            var level = parseInt($(this).val());
            if (level < min) min = level;
            if (level > max) max = level;
        });
        if (min < 999) {
            input += " >=" + min;
        }
        if (max > 0) {
            input += " <" + (max + 100);
        }
        if ($("#advanced_instructor").val().trim().length != 0) {
            input += " " + $("#advanced_instructor").val();
        }
        if ($("#advanced_title").val().trim().length != 0) {
            input += " " + $("#advanced_title").val();
        }
        boxes = $("input[name=day]:checked");
        boxes.each(function(){
            input += " " + $(this).val();
        });
        boxes = $("input[name=time]:checked");
        boxes.each(function(){
            input += " " + $(this).val();
        });
        boxes = $("input[name=dist]:checked");
        boxes.each(function(){
            input += " " + $(this).val();
        });
        if ($("#advanced_keyword").val().trim().length != 0) {
            input += " " + $("#advanced_keyword").val();
        }
        
        $("#omnibar_input").val(input);
        $("#omnibar_input").submit();
        $("#advanced_search").fadeOut();
        $("#advanced_search_wrapper").fadeOut();
        $("#advanced_search_wrapper").unbind('click');
    });

    /* Attach a handler to the preset search button */
    $("#preset_search_1").click(function() {
        $("#omnibar_input").val("pdf-only");
        $("#omnibar_input").submit();
    });
    
    /* handle checking and unchecking the show old courses checkbox */
    $("#omnibar_showold").change(function() {
        /* handle if just checked */
        if ($(this).is(":checked")) {
            $(".course_old").css("display","");
        }
        else if (!$(this).is(":checked")) {
            $(".course_old").css("display","none");
        }
    });
    
    /* attach a submit handler to the form */
    $("#omnibar_form").submit(function(event) {
        /* stop form from submitting normally */
        event.preventDefault();
        
        /* If the request hasn't changed, don't re-send it */
        if ($("#omnibar_previous").text() == $("#omnibar_input").val())
            return;
        /* If the request has changed (or is the first one), save it in
         * a hidden form input */
        $("#omnibar_previous").text($("#omnibar_input").val());

        /* make the spinner */
        var spinner;
        if (!spinner_on) {
            spinner = make_spinner();
            spinner_on = true;
        }
        
        /* send the data using post */
        var posting = $.post("/results/", $("#omnibar_form").serialize(), 
            function( data ) {
                /* put the data in the result div */
                $("#results_div").empty().append( $( data ) );
                
                /* don't show old courses if the check box isn't checked */
                if(!$("#omnibar_showold").is(":checked")) $(".course_old").css("display","none");
                
                /* give the results divs a fancy scrollbar */
                $("#results_left_div").jScrollPane({showArrows:true, hideFocus:true, autoReinitialise:true});
                $("#results_right_div").jScrollPane({showArrows:true, hideFocus:true, autoReinitialise:true});
                
                /* Enable showing cart courses */
                $(".coursecart").click(function(ev){
                    if ($(ev.target).attr("type") == "submit") return;
                    var course_id = this.id.split('_')[2];
                    display(course_id);
                });
                
                /* make the course's data show up when it is clicked */
                $(".course").click(function() {
                    $("#right_scrollbar_wrap").css("background-color","rgba(0,0,0,0.9)");
                    var course_id = $(this).attr('id').split('_')[2];
                    display(course_id);  
                });
                
                /* set the behavior of the "load semester button" */
                $(".semester_menu>.term_selector>.term_dropdown").change(function() {
                    var params = $(this).find("option:selected").attr('class').split('_');
                    load_semester(params);
                });
                
                $(".semester_menu>.reviews_form").submit(function(ev) {
                    ev.preventDefault();
                    var course_id = $(this).find("input[name=course_id]").attr('value');
                    load_reviews(course_id);
                });
                
                /* set the behavior of the "save course to cart button" */
                $(".savecourse_form").submit(function(ev) {
                    ev.preventDefault();
                    /* Disable the submit button */
                    $("input[type=submit]", this).attr("disabled", "disabled").css("visibility","hidden");
                    
                    var posting = $.post("/course/add/", $(this).serialize(), function( data ) {
                        $("#cart_list").append(data);
                        
                        /* redisplay course information when user selects it in his/her cart */
                        $(".coursecart").click(function(ev){
                            if ($(ev.target).attr("type") == "submit") return;
                            var course_id = this.id.split('_')[2];
                            $("#right_scrollbar_wrap").css("background-color","rgba(0,0,0,0.9)");
                            display(course_id);
                        });
                        
                        /*set behavior of remove from cart button */
                        $(".removecourse_form").submit(function(e) {
                            e.preventDefault();
                            var course_id = $(this).parent().attr('id').split('_')[2];
                            /* send post request to save that the user has removed the course from his/her cart */
                            var posting = $.post("/course/remove/", $(this).serialize());
                            /* remove the course from the cart list */
                            $("#cart_num_"+course_id).remove();
                            /* if in result list activate save button */
                            if ($("#result_num_"+course_id).length > 0) {
                                $("#save_"+course_id+">input[type=submit]").removeAttr("disabled").css("visibility","visible");
                            }
                            /* Otherwise delete course result */
                            else {
                                $("#detail_num_"+course_id).remove();
                            }
                        });
                    });
                }); 
                
                //stop the spinner 
                if (spinner_on) {
                    spinner.stop();
                    spinner_on = false;
                }
            });
    });
});
