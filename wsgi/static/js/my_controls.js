MyControls = function ( object, domElement ) {

    this.object = object;
    this.object.position =
    this.target = new THREE.Vector3( 0, 10, -50 );

    this.domElement = ( domElement !== undefined ) ? domElement : document;

    this.movementSpeed = 30.0;
    this.lookSpeed = 0.2;

    this.mouseX = 0;
    this.mouseY = 0;

    this.moveForward = false;
    this.moveBackward = false;
    this.moveLeft = false;
    this.moveRight = false;

    this.mouse_movement = false;

    this.mouseDragOn = false;

    this.viewHalfX = 0;
    this.viewHalfY = 0;

    if ( this.domElement !== document ) {
        this.domElement.setAttribute( 'tabindex', -1 );
    }


    this.handleResize = function () {
        if ( this.domElement === document ) {
            this.viewHalfX = window.innerWidth / 2;
            this.viewHalfY = window.innerHeight / 2;
        } else {
            this.viewHalfX = this.domElement.offsetWidth / 2;
            this.viewHalfY = this.domElement.offsetHeight / 2;
        }
    };


    this.onMouseDown = function ( event ) {
        if ( this.domElement !== document ) {
            this.domElement.focus();
        }
        event.preventDefault();
        event.stopPropagation();

        switch ( event.button ) {
            case 0: this.moveForward = true; break;
            case 2: this.moveBackward = true; break;
        }
        this.mouseDragOn = true;
    };


    this.onMouseUp = function ( event ) {

        event.preventDefault();
        event.stopPropagation();

        switch ( event.button ) {
            case 0: this.moveForward = false; break;
            case 2: this.moveBackward = false; break;
        }
        this.mouseDragOn = false;
    };


    this.onMouseMove = function ( event ) {

        if ( this.domElement === document ) {
            this.mouseX = event.pageX - this.viewHalfX;
            this.mouseY = event.pageY - this.viewHalfY;
        } else {
            this.mouseX = event.pageX - this.domElement.offsetLeft - this.viewHalfX;
            this.mouseY = event.pageY - this.domElement.offsetTop - this.viewHalfY;
        }
        this.mouse_movement = true;
    };


    this.onKeyDown = function ( event ) {

        //event.preventDefault();
        switch ( event.keyCode ) {
            case 38: /*up*/
            case 87: /*W*/  this.moveForward = true; break;
            case 37: /*left*/
            case 65: /*A*/  this.moveLeft = true; break;
            case 40: /*down*/
            case 83: /*S*/  this.moveBackward = true; break;
            case 39: /*right*/
            case 68: /*D*/  this.moveRight = true; break;
        }
    };


    this.onKeyUp = function ( event ) {

        switch( event.keyCode ) {
            case 38: /*up*/
            case 87: /*W*/  this.moveForward = false; break;
            case 37: /*left*/
            case 65: /*A*/  this.moveLeft = false; break;
            case 40: /*down*/
            case 83: /*S*/  this.moveBackward = false; break;
            case 39: /*right*/
            case 68: /*D*/  this.moveRight = false;
        }
    };


    this.update = function( delta ) {

        var actualMoveSpeed = delta * this.movementSpeed;

        if ( this.moveForward ) this.object.position.setZ( this.object.position.z - actualMoveSpeed);
        if ( this.moveBackward ) this.object.position.setZ( this.object.position.z + actualMoveSpeed );
        if ( this.moveLeft ) this.object.position.setX(this.object.position.x - actualMoveSpeed );
        if ( this.moveRight ) this.object.position.setX(this.object.position.x + actualMoveSpeed );

        if (this.mouse_movement == true) {
            this.object.rotation.x = Math.max(-this.mouseY / this.viewHalfY, -.6) * this.lookSpeed;
            this.object.rotation.y = -this.mouseX / this.viewHalfX * this.lookSpeed * 2;
            this.mouse_movement = false;
        }
    };

    this.domElement.addEventListener( 'contextmenu', function ( event ) { event.preventDefault(); }, false );
    this.domElement.addEventListener( 'mousemove', bind( this, this.onMouseMove ), false );
    this.domElement.addEventListener( 'mousedown', bind( this, this.onMouseDown ), false );
    this.domElement.addEventListener( 'mouseup', bind( this, this.onMouseUp ), false );

    window.addEventListener( 'keydown', bind( this, this.onKeyDown ), false );
    window.addEventListener( 'keyup', bind( this, this.onKeyUp ), false );

    function bind( scope, fn ) {

        return function () {

            fn.apply( scope, arguments );

        };

    };

    this.handleResize();

};

