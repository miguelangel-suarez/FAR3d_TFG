      subroutine zgegs(JOBVSL, JOBVSR, N, A, LDA, B, LDB, ALPHA, BETA,
     $     VSL, LDVSL, VSR, LDVSR, WORK, LWORK, RWORK,
     $     INFO )

       CHARACTER          JOBVSL, JOBVSR
       INTEGER            INFO, LDA, LDB, LDVSL, LDVSR, LWORK, N

       DOUBLE PRECISION   RWORK( * )
       COMPLEX*16         A( LDA, * ), ALPHA( * ), B( LDB, * ),
     $     beta( * ), vsl( ldvsl, * ), vsr( ldvsr, * ),
     $     work( * )
 
       DOUBLE PRECISION   ZERO, ONE
       PARAMETER          ( ZERO = 0.0d0, one = 1.0d0 )
       COMPLEX*16         CZERO, CONE
       parameter( czero = ( 0.0d0, 0.0d0 ),
     $     cone = ( 1.0d0, 0.0d0 ) )

       LOGICAL            ILASCL, ILBSCL, ILVSL, ILVSR, LQUERY
       INTEGER            ICOLS, IHI, IINFO, IJOBVL, IJOBVR, ILEFT, ILO,
     $     iright, irows, irwork, itau, iwork, lopt,
     $     lwkmin, lwkopt, nb, nb1, nb2, nb3
       DOUBLE PRECISION   ANRM, ANRMTO, BIGNUM, BNRM, BNRMTO, EPS,
     $     SAFMIN, SMLNUM

       EXTERNAL           xerbla, zgeqrf, zggbak, zggbal, zgghrd, zhgeqz,
     $     zlacpy, zlascl, zlaset, zungqr, zunmqr

       LOGICAL            LSAME
       INTEGER            ILAENV
       DOUBLE PRECISION   DLAMCH, ZLANGE
       EXTERNAL           lsame, ilaenv, dlamch, zlange

       INTRINSIC          int, max

       IF( lsame( jobvsl, 'N' ) ) THEN
          ijobvl = 1
          ilvsl = .false.
       ELSE IF( lsame( jobvsl, 'V' ) ) THEN
          ijobvl = 2
          ilvsl = .true.
       ELSE
          ijobvl = -1
          ilvsl = .false.
       END IF
 
       IF( lsame( jobvsr, 'N' ) ) THEN
          ijobvr = 1
          ilvsr = .false.
       ELSE IF( lsame( jobvsr, 'V' ) ) THEN
          ijobvr = 2
          ilvsr = .true.
       ELSE
          ijobvr = -1
          ilvsr = .false.
       END IF

       lwkmin = max( 2*n, 1 )
       lwkopt = lwkmin
       work( 1 ) = lwkopt
       lquery = ( lwork == -1 )
       info = 0
       IF( ijobvl.LE.0 ) THEN
          info = -1
       ELSE IF( ijobvr.LE.0 ) THEN
          info = -2
       ELSE IF( n.LT.0 ) THEN
          info = -3
       ELSE IF( lda.LT.max( 1, n ) ) THEN
          info = -5
       ELSE IF( ldb.LT.max( 1, n ) ) THEN
          info = -7
       ELSE IF( ldvsl.LT.1 .OR. ( ilvsl .AND. ldvsl.LT.n ) ) THEN
          info = -11
       ELSE IF( ldvsr.LT.1 .OR. ( ilvsr .AND. ldvsr.LT.n ) ) THEN
          info = -13
       ELSE IF( lwork.LT.lwkmin .AND. .NOT.lquery ) THEN
          info = -15
       END IF
 
       IF( info == 0 ) THEN
          nb1 = ilaenv( 1, 'ZGEQRF', ' ', n, n, -1, -1 )
          nb2 = ilaenv( 1, 'ZUNMQR', ' ', n, n, n, -1 )
          nb3 = ilaenv( 1, 'ZUNGQR', ' ', n, n, n, -1 )
          nb = max( nb1, nb2, nb3 )
          lopt = n*( nb+1 )
          work( 1 ) = lopt
       END IF
 
       IF( info.NE.0 ) THEN
          CALL xerbla( 'ZGEGS ', -info )
          RETURN
       ELSE IF( lquery ) THEN
          RETURN
       END IF

       IF( n == 0 )
     $     RETURN

       eps = dlamch( 'E' )*dlamch( 'B' )
       safmin = dlamch( 'S' )
       smlnum = n*safmin / eps
       bignum = one / smlnum

       anrm = zlange( 'M', n, n, a, lda, rwork )
       ilascl = .false.
       IF( anrm.GT.zero .AND. anrm.LT.smlnum ) THEN
          anrmto = smlnum
          ilascl = .true.
       ELSE IF( anrm.GT.bignum ) THEN
          anrmto = bignum
          ilascl = .true.
       END IF
 
       IF( ilascl ) THEN
          CALL zlascl( 'G', -1, -1, anrm, anrmto, n, n, a, lda, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
       END IF

       bnrm = zlange( 'M', n, n, b, ldb, rwork )
       ilbscl = .false.
       IF( bnrm.GT.zero .AND. bnrm.LT.smlnum ) THEN
          bnrmto = smlnum
          ilbscl = .true.
       ELSE IF( bnrm.GT.bignum ) THEN
          bnrmto = bignum
          ilbscl = .true.
       END IF
 
       IF( ilbscl ) THEN
          CALL zlascl( 'G', -1, -1, bnrm, bnrmto, n, n, b, ldb, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
       END IF

       ileft = 1
       iright = n + 1
       irwork = iright + n
       iwork = 1
       CALL zggbal( 'P', n, a, lda, b, ldb, ilo, ihi, rwork( ileft ),
     $     rwork( iright ), rwork( irwork ), iinfo )
       IF( iinfo.NE.0 ) THEN
          info = n + 1
          goto 100
       END IF

       irows = ihi + 1 - ilo
       icols = n + 1 - ilo
       itau = iwork
       iwork = itau + irows
       CALL zgeqrf( irows, icols, b( ilo, ilo ), ldb, work( itau ),
     $     work( iwork ), lwork+1-iwork, iinfo )
       IF( iinfo.GE.0 )
     $     lwkopt = max( lwkopt, int( work( iwork ) )+iwork-1 )
       IF( iinfo.NE.0 ) THEN
          info = n + 2
          goto 100
       END IF
 
       CALL zunmqr( 'L', 'C', irows, icols, irows, b( ilo, ilo ), ldb,
     $     work( itau ), a( ilo, ilo ), lda, work( iwork ),
     $     lwork+1-iwork, iinfo )
       IF( iinfo.GE.0 )
     $     lwkopt = max( lwkopt, int( work( iwork ) )+iwork-1 )
       IF( iinfo.NE.0 ) THEN
          info = n + 3
          goto 100
       END IF
 
       IF( ilvsl ) THEN
          CALL zlaset( 'Full', n, n, czero, cone, vsl, ldvsl )
          CALL zlacpy( 'L', irows-1, irows-1, b( ilo+1, ilo ), ldb,
     $     vsl( ilo+1, ilo ), ldvsl )
          CALL zungqr( irows, irows, irows, vsl( ilo, ilo ), ldvsl,
     $     work( itau ), work( iwork ), lwork+1-iwork,
     $     iinfo )
          IF( iinfo.GE.0 )
     $     lwkopt = max( lwkopt, int( work( iwork ) )+iwork-1 )
          IF( iinfo.NE.0 ) THEN
             info = n + 4
             goto 100
          END IF
       END IF
 
       IF( ilvsr )
     $     CALL zlaset( 'Full', n, n, czero, cone, vsr, ldvsr )

       CALL zgghrd( jobvsl, jobvsr, n, ilo, ihi, a, lda, b, ldb, vsl,
     $     ldvsl, vsr, ldvsr, iinfo )
       IF( iinfo.NE.0 ) THEN
          info = n + 5
          goto 100
       END IF

       iwork = itau
       CALL zhgeqz( 'S', jobvsl, jobvsr, n, ilo, ihi, a, lda, b, ldb,
     $     alpha, beta, vsl, ldvsl, vsr, ldvsr, work( iwork ),
     $     lwork+1-iwork, rwork( irwork ), iinfo )
       IF( iinfo.GE.0 )
     $     lwkopt = max( lwkopt, int( work( iwork ) )+iwork-1 )
       IF( iinfo.NE.0 ) THEN
          IF( iinfo.GT.0 .AND. iinfo.LE.n ) THEN
             info = iinfo
          ELSE IF( iinfo.GT.n .AND. iinfo.LE.2*n ) THEN
             info = iinfo - n
          ELSE
             info = n + 6
          END IF
          goto 100
       END IF

       IF( ilvsl ) THEN
          CALL zggbak( 'P', 'L', n, ilo, ihi, rwork( ileft ),
     $     rwork( iright ), n, vsl, ldvsl, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 7
             goto 100
          END IF
       END IF
       IF( ilvsr ) THEN
          CALL zggbak( 'P', 'R', n, ilo, ihi, rwork( ileft ),
     $     rwork( iright ), n, vsr, ldvsr, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 8
             goto 100
          END IF
       END IF

       IF( ilascl ) THEN
          CALL zlascl( 'U', -1, -1, anrmto, anrm, n, n, a, lda, iinfo)
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
          CALL zlascl( 'G', -1, -1, anrmto, anrm, n, 1, alpha, n, iinfo)
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
       END IF
 
       IF( ilbscl ) THEN
          CALL zlascl( 'U', -1, -1, bnrmto, bnrm, n, n, b, ldb, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
          CALL zlascl( 'G', -1, -1, bnrmto, bnrm, n, 1, beta, n, iinfo )
          IF( iinfo.NE.0 ) THEN
             info = n + 9
             RETURN
          END IF
       END IF
 
 100  continue
       work( 1 ) = lwkopt
 
       RETURN

       END