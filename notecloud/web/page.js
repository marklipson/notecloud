(function($){
  // currently open file
  var current_path = "";

  function read_note(path, send_to) {
    $.ajax({
        url: "/api/note/" + encodeURI(path),
        method: "get",
        dataType: "json"
    }).done(function(resp){
        send_to(resp);
    });
  }
  function write_note(path, content, on_stored) {
    $.ajax({
        url: "/api/note/" + encodeURI(path),
        method: "post",
        data: content,
        dataType: "json"
    }).done(function(resp){
        on_stored(resp.path, resp.props);
    });
  }
  function search_notes(spec, results_to) {
    $.ajax({
        url: "/api/note/",
        data: {spec: spec},
        method: "get",
        dataType: "json"
    }).done(function(resp){
        results_to(resp.results, resp.highlights);
    });
  }
  function format_age(age) {
    age = Math.round(age);
    if (age < 60)
        return "< 1m";
    if (age < 3600)
        return Math.round(age/60) + "m";
    if (age < 86400)
        return Math.round(age/360)/10 + "h";
    if (age < 86400*365)
        return Math.round(age/8640)/10 + "d";
    return Math.round(age/86400*36.52425)/10 + "y";
  }
  function draw_preview(elem, note, highlights)
  {
    var note_content = note.content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;');
    // highlight terms
    for (var n=0; n < highlights.length; n++)
    {
        var rx = new RegExp(highlights[n], "gi");
        note_content = note_content.replace(rx, "<span class='highlight'>$1</span>");
    }
    elem.text("");
    var tools = $("<div>" ).addClass("pvw-tools");
    var t_open_l = $("<button>").text('< open' ).click(function(){
        window.open("/index.html#" + note.path)
    });
    var t_open_r = $("<button>").text('open >' ).click(function(){
        window.open("/index.html#" + note.path, "_blank")
    });
    tools.append(t_open_l ).append(t_open_r);
    elem.append(tools);
    var title = $("<div>").addClass("pvw-title" ).text(note.props.title);
    elem.append(title);
    var content = $("<div>").addClass("pvw-content").html(note_content);
    elem.append(content);
  }
  function hover_preview(elem, path, highlights)
  {
    if (! path)
      return;
    var pvw = $("#preview");
    var tmr = null;
    var tmr0 = null;
    var open = false;
    function h_pvw_1(){
        if (open && tmr0)
            clearTimeout(tmr0);
    }
    function h_pvw_0(){
        if (open)
            rqst_0();
    }
    function do_hover() {
        // if it's being edited don't show the preview
        if ($(".result[data-path='"+path+"']").hasClass("editing"))
          return;
        open = true;
        pvw.fadeIn();
        elem.addClass("previewing");
        pvw.bind("mouseover", h_pvw_1);
        pvw.bind("mouseout", h_pvw_0);
        // open the preview
        read_note(path, function(note){
            draw_preview(pvw, note, highlights);
        });
    }
    function un_hover() {
        open = false;
        pvw.fadeOut();
        elem.removeClass("previewing");
        pvw.unbind("mouseover", h_pvw_1);
        pvw.unbind("mouseout", h_pvw_0);
    }
    function rqst_1() {
        if (! tmr)
            tmr = setTimeout(do_hover, 750);
        if (tmr0)
            clearTimeout(tmr0);
        tmr0 = null;
    }
    function rqst_0() {
        if (tmr)
            clearTimeout(tmr);
        tmr = null;
        tmr0 = setTimeout(un_hover, 150);
    }
    elem.mouseover(rqst_1);
    elem.mouseout(rqst_0);
  }
  function draw_results(results, resultsarea, open_file, highlights){
    resultsarea.text("");
    for (var n=0; n < results.length; n++)
    {
        var result = results[n];
        var descr = $("<div>").addClass("result").attr("data-path", result.path);
        if (result.path == current_path)
          descr.addClass("editing");
        var d_title = $("<span>").addClass("result-title" ).text(result.props.title);
        var d_age = $("<span>" ).addClass("result-age").text(format_age(result.props.age));
        var d_folder = $("<span>" ).addClass("result-folder").text(result.props.folder);
        descr.append(d_title).append(d_age ).append(d_folder);
        resultsarea.append(descr);
        descr.click(function(){
            var path = $(this).attr("data-path");
            var title = $(this).find(".result-title").text();
            open_file(path, title);
            $("#preview").hide();
        });
        hover_preview(descr, result.path, highlights);
    }
  }
  function setup_autosearch(searchbox, resultsarea, searchbutton, clearsearch, open_file) {
    var active = null;
    var prev_spec = null;
    function do_search(force){
        var spec = searchbox.val();
        if (spec != prev_spec || force)
        {
            prev_spec = spec;
            search_notes(spec, function(results, highlights){
                draw_results(results, resultsarea, open_file, highlights);
            });
        }
    }
    function request_search(force){
        if (active)
            clearTimeout(active);
        active = setTimeout(function() {
          do_search(force);
        }, 500);
    }
    function setup_refresh_autosearch()
    {
      // as long as mouse is not over search area, refresh search every so often
      var mouse_over_search = false;
      $("#search" ).mouseover(function(){
        mouse_over_search = true;
      }).mouseout(function(){
        mouse_over_search = false;
      });
      setInterval(function(){
        if (! mouse_over_search)
          request_search(1);
      }, 15000 );
    }
    searchbox.keyup(request_search);
    searchbutton.click(function(){ do_search(true); });
    clearsearch.click(function(){
      searchbox.val("");
      request_search();
    });
    // do an initial search to show recent entries
    do_search(1);
    // keep search results up to date
    setup_refresh_autosearch();
  }
  function setup_editor(edittitle, editprops, editbox, newbutton, editorstatus){
    var active = null;
    var prev_content = null;
    function update_props(props){
        var msg = "";
        if (props.folder)
            msg += "folder: " + props.folder;
        if (props.tag)
        {
            if (msg)
                msg += ", ";
            msg += "tags: ";
            for (var n = 0; n < props.tag.length; n++)
            {
                msg += " ";
                msg += props.tag[n];
            }
        }
        editprops.text(msg);
        edittitle.text(props.title);
    }
    function do_save(after){
        var content = editbox.val();
        if (content != prev_content)
        {
            prev_content = content;
            write_note(current_path || "", content, function(path, props){
                current_path = content ? path : "";
                window.location.hash = current_path;
                update_props(props);
                editorstatus.text("all changes saved");
                if (after)
                  after();
            });
        }
        else {
          editorstatus.text("all changes saved");
          if (after)
            after();
        }
    }
    function request_save(){
        // TODO look for "?[fs...] at BOL
        // TODO strip those out of the content
        // TODO do things based on those commands
        editorstatus.text("SAVING...");
        if (active)
            clearTimeout(active);
        active = setTimeout(do_save, 500);
    }
    function open_file(path){
        do_save(function(){
            read_note(path, function(note){
                current_path = path;
                window.location.hash = path;
                prev_content = note.content;
                editbox.val(note.content);
                update_props(note.props);
                // show in search results
                $(".result.editing").removeClass("editing");
                $(".result[data-path='"+path+"']").addClass("editing")
            });
        });
    }
    editbox.keyup(request_save);
    newbutton.click(function(){
        do_save(function(){
            current_path = "";
            prev_content = null;
            edittitle.text("");
            editprops.text("");
            editbox.val("");
        });
    });
    $("#deletefile").click(function(){
      if (! current_path)
        return;
      if (confirm("Are you sure you want to delete " + current_path + "?")){
        // resetting content causes file to be deleted
        $("#maineditor" ).val("");
        request_save();
      }
    });
    return open_file;
  }
  function setup_autohash(open_file){
    function goto_hash()
    {
        var h = window.location.hash;
        if (h.match( new RegExp("^#") ))
            h = h.substr(1);
        if (h)
            open_file(h);
    }
    // track hash, to support browser back/forward buttons
    $(window).on('hashchange',function(){
        goto_hash();
    });
    // go to initial hash location
    goto_hash();
  }
  $(function(){
    var open_file = setup_editor($(".edittitle"), $(".editprops"), $("#maineditor"), $("#newfile"), $(".editorstatus"));
    setup_autosearch($("#searchbox"), $("#searchresults"), $("#searchbutton"), $("#clearsearch"), open_file);
    setup_autohash(open_file);
  });

})(jQuery);
