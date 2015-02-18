tree:
    li      $t0, 3
    li      $t1, 2
    li      $t2, 6
    li      $t3, 30
    li      $t4, -30
    li      $t5, 25
    li      $t6, -25

    cs
    li      $a0, 450
    jall    tree_fun
    jl      done

tree_fun:
    addi    $sp, $sp, -24
    sw      $ra,  0($sp)
    sw      $s0,  8($sp)
    sw      $s7, 16($sp)

    add     $s0, $a0, $zero
    addi    $s7, $s7, 1

    slti    $t7, $s0, 15
    beql    $t7, $zero, tree_cont

tree_cond:
    fd      $s0
    sub     $t7, $zero, $s0
    fd      $t7

tree_exit:
    lw      $ra,  0($sp)
    lw      $s0,  8($sp)
    lw      $s7, 16($sp)
    addi    $sp, $sp, 24
    jr      $ra

tree_cont:
    add     $t9, $s0, $zero
    div     $t9, $t0
    fd      $t9

    rt      $t4
    add     $t9, $s0, $zero
    mult    $t9, $t1
    div     $t9, $t0
    add     $a0, $t9, $zero
    jall    tree_fun
    rt      $t3

    add     $t9, $s0, $zero
    div     $t9, $t2
    fd      $t9

    rt      $t5
    add     $t9, $s0, $zero
    div     $t9, $t1
    add     $a0, $t9, $zero
    jall    tree_fun
    rt      $t6

    add     $t9, $s0, $zero
    div     $t9, $t0
    fd      $t9

    rt      $t5
    add     $t9, $s0, $zero
    div     $t9, $t1
    add     $a0, $t9, $zero
    jall    tree_fun
    rt      $t6

    add     $t9, $s0, $zero
    div     $t9, $t2
    fd      $t9

    sub     $t9, $zero, $s0
    fd      $t9

    jl      tree_exit

done:
